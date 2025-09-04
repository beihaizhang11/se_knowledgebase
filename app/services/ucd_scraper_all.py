"""
UCD 成绩抓取（与 TS 测试完全对齐的 Python 版）
- 登录 → RG160-1R → 抓取所有 RG160-2R → 解析 studentInfo / stageResults / courseWork
- 字段命名与 TS 保持一致（含 resultsUrl，并兼容 results_url）
"""

import asyncio
import logging
import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

logger = logging.getLogger(__name__)


def _norm(s: str) -> str:
    return (s or "").replace("\u00a0", " ").strip()


class UCDScraper:
    def __init__(self, username: str, password: str, base_url: str = "https://hub.ucd.ie/usis/"):
        if not username or not password:
            raise ValueError("请提供 UCD 账号和密码")
        self.username = username
        self.password = password
        self.base_url = base_url

    # ---------------------------- 公共工具 ----------------------------
    def _to_abs(self, href: str) -> str:
        return urljoin(self.base_url, href or "")

    # ---------------------------- 主流程 ----------------------------
    async def get_all_results(self) -> List[Dict[str, Any]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await self._login(page)
                summary_rows = await self._get_results_summary(page)  # 与 TS 相同字段
                all_results: List[Dict[str, Any]] = []

                # 逐个进入每个 resultsUrl，解析详情（保持同一会话）
                for row in summary_rows:
                    url = row.get("resultsUrl") or row.get("results_url") or ""
                    if not url:
                        continue
                    await page.goto(url, wait_until="domcontentloaded")
                    await page.wait_for_load_state("networkidle")
                    # 与 TS 测试的断言等价：URL 中应包含 p_report=RG160-2R
                    if not re.search(r"p_report=RG160-2R", page.url, re.I):
                        raise RuntimeError("未进入 RG160-2R 页面")

                    detail = await self._parse_rg160_2r(page)
                    all_results.append({"summary": row, "detail": detail})

                logger.info("ALL results detail parsed: %d", len(all_results))
                return all_results

            finally:
                await browser.close()

    # ---------------------------- 登录流程（与 TS 相同等待点） ----------------------------
    async def _login(self, page):
        await page.goto(f"{self.base_url}W_WEB_WELCOME_PAGE", wait_until="domcontentloaded")

        # Cookie 弹窗（与 TS 同逻辑：可见才点）
        try:
            accept = page.get_by_role("button", name=re.compile(r"accept all cookies", re.I))
            if await accept.is_visible():
                await accept.click()
        except Exception:
            pass

        # 进入登录
        await page.get_by_role("link", name=re.compile(r"log in with ucd connect", re.I)).click()
        await page.get_by_role("textbox", name=re.compile(r"username", re.I)).fill(self.username)
        await page.get_by_role("textbox", name=re.compile(r"password", re.I)).fill(self.password)

        # 等待跳到 SI-HOME（90s），与 TS 一致
        await asyncio.gather(
            page.wait_for_url(re.compile(r"W_HU_MENU\.P_DISPLAY_MENU.*p_menu=SI-HOME", re.I), timeout=90_000),
            page.get_by_role("button", name=re.compile(r"login", re.I)).click(),
        )
        await page.wait_for_load_state("networkidle")

    # ---------------------------- 汇总页解析（RG160-1R） ----------------------------
    async def _get_results_summary(self, page) -> List[Dict[str, Any]]:
        # 找 Registration
        reg_locator = page.locator(
            'a[href*="W_HU_MENU.P_DISPLAY_MENU"][href*="p_menu=SI-REGISTRATION"]'
        ).first
        await reg_locator.wait_for(state="visible")
        reg_href = await reg_locator.get_attribute("href")
        if not reg_href:
            raise RuntimeError("Registration 链接 href 为空")
        await page.goto(self._to_abs(reg_href), wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        # 进入 RG160-1R
        results_locator = page.locator(
            'a[href*="W_HU_REPORTING.P_DISPLAY_REPORT"][href*="p_report=RG160-1R"]'
        ).first
        await results_locator.wait_for(state="visible")
        results_href = await results_locator.get_attribute("href")
        if not results_href:
            raise RuntimeError("RG160-1R 链接 href 为空")
        await page.goto(self._to_abs(results_href), wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")

        # 确认表存在
        await page.wait_for_selector("#RG160-1Q", timeout=15_000)

        # 与 TS 中 $$eval 逻辑一致：term/stage/year/programme/major/href
        summary: List[Dict[str, Any]] = await page.evaluate(
            """
            () => {
              const toText = el => ((el?.textContent ?? '')
                  .replace(/\\u00a0/g, ' ')
                  .replace(/\\s+/g, ' ')
                  .trim());
              const trs = Array.from(document.querySelectorAll('#RG160-1Q tbody tr'));
              return trs.map(tr => {
                const tds = Array.from(tr.querySelectorAll('td'));
                const term = toText(tds[0]);
                const stage = toText(tds[1]);
                const year = toText(tds[2]);
                const programme = toText(tds[3]);
                const majorHtml = (tds[4]?.innerHTML ?? '').replace(/<br\\s*\\/?>/gi, ' ');
                const major = majorHtml.replace(/<[^>]+>/g, '').replace(/\\u00a0/g, ' ')
                  .replace(/\\s+/g, ' ').trim();
                const linkEl = tds[5]?.querySelector('a[href*="p_report=RG160-2R"]');
                const href = linkEl?.getAttribute('href') ?? '';
                return { term, stage, year, programme, major, href };
              });
            }
            """
        )

        # 相对 → 绝对；字段名与 TS 一致（resultsUrl），并兼容 results_url
        for row in summary:
            abs_url = self._to_abs(row.get("href", ""))
            row["resultsUrl"] = abs_url
            row["results_url"] = abs_url  # 兼容你前端旧字段

        if not summary:
            raise RuntimeError("没有获取到成绩数据")

        logger.info("Summary rows: %s", summary)
        return summary

    # ---------------------------- 详情页解析（RG160-2R） ----------------------------
    async def _parse_rg160_2r(self, page) -> Dict[str, Any]:
        # TS 中先短等课程表，再 networkidle
        try:
            await page.wait_for_selector("#RG160-20Q", timeout=20_000)
        except PWTimeoutError:
            pass
        await page.wait_for_load_state("networkidle")

        # 1) 学生信息（studentInfo）
        student_info: Dict[str, Any] = await page.evaluate(
            """
            () => {
              const norm = s => (s || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();

              const grabKVs = (tableId) => {
                const t = document.querySelector(`table#${CSS.escape(tableId)}`);
                if (!t) return {};
                const out = {};
                for (const tr of Array.from(t.querySelectorAll('tr'))) {
                  const th = tr.querySelector('th');
                  const td = tr.querySelector('td');
                  if (!th || !td) continue;
                  const key = norm((th.textContent || '').replace(/:$/, ''));
                  const val = norm(td.innerText || td.textContent || '');
                  out[key] = val;
                }
                return out;
              };

              const a = grabKVs('RG160-2');   // Degree / Programme / Semester GPA
              const b = grabKVs('RG160-2T');  // Degree / Programme / Degree Result

              const info = {};
              if (a['Degree']) info['degree'] = a['Degree'];
              if (a['Programme']) info['programme'] = a['Programme'];
              if (a['Semester GPA']) info['semesterGpa'] = a['Semester GPA'];
              if (b['Degree Result']) info['degreeResult'] = b['Degree Result'];
              return info;
            }
            """
        )

        # 2) 阶段汇总（stageResults）——字段与 TS 一致
        stage_results: List[Dict[str, str]] = await page.evaluate(
            """
            () => {
              const norm = s => (s || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
              const rows = [];
              const trs = Array.from(document.querySelectorAll('#RG160-5Q tbody tr'));
              for (const tr of trs) {
                const tds = Array.from(tr.querySelectorAll('td'));
                if (!tds.length) continue;
                rows.push({
                  major:            norm(tds[0]?.innerText || tds[0]?.textContent || ''),
                  stage:            norm(tds[1]?.innerText || ''),
                  status:           norm(tds[2]?.innerText || ''),
                  attemptedCredits: norm(tds[3]?.innerText || ''),
                  earnedCredits:    norm(tds[4]?.innerText || ''),
                  stageGpa:         norm(tds[5]?.innerText || ''),
                  award:            norm(tds[6]?.innerText || ''),
                  awardDescription: norm(tds[7]?.innerText || ''),
                  awardGpa:         norm(tds[8]?.innerText || ''),
                });
              }
              return rows;
            }
            """
        )

        # 3) 课程明细（courseWork）——字段与 TS 一致
        course_work: List[Dict[str, str]] = await page.evaluate(
            """
            () => {
              const base = 'https://hub.ucd.ie/usis/';
              const norm = s => (s || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim();
              const rows = [];
              const trs = Array.from(document.querySelectorAll('#RG160-20Q tbody tr'));
              for (const tr of trs) {
                const tds = Array.from(tr.querySelectorAll('td'));
                if (!tds.length) continue;
                const a = tds[1]?.querySelector('a');
                const crnText = norm(a?.textContent || tds[1]?.textContent || '');
                const crnHref = a?.getAttribute('href') || '';
                const crnUrl  = crnHref ? new URL(crnHref, base).toString() : '';
                rows.push({
                  semester:              norm(tds[0]?.innerText || ''),
                  crn:                   crnText,
                  crnUrl,
                  module:                norm(tds[2]?.innerText || ''),
                  moduleTitle:           norm(tds[3]?.innerText || ''),
                  stage:                 norm(tds[4]?.innerText || ''),
                  credits:               norm(tds[5]?.innerText || ''),
                  grade:                 norm(tds[6]?.innerText || ''),
                  compensationAvailable: norm(tds[7]?.innerText || ''),
                });
              }
              return rows;
            }
            """
        )

        return {
            "studentInfo": student_info,
            "stageResults": stage_results,
            "courseWork": course_work,
        }


# --------------------- 给 Flask 使用的封装 ---------------------

async def get_ucd_all_results(username: str, password: str) -> List[Dict[str, Any]]:
    """
    - 返回结构：[{ summary: SummaryRow, detail: ResultDetail }, ...]
    - SummaryRow 包含 resultsUrl（并同时带 results_url 兼容你的前端）
    """
    scraper = UCDScraper(username=username, password=password)
    return await scraper.get_all_results()
