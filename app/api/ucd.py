# app/api/ucd.py
from flask import Blueprint, jsonify, request
import asyncio
import logging


from app.services.ucd_scraper_all import get_ucd_all_results, UCDScraper

logger = logging.getLogger(__name__)
ucd_bp = Blueprint('ucd', __name__, url_prefix='/api/ucd')


@ucd_bp.route('/results', methods=['POST'])
def get_results():
    """
    接收前端提交的 UCD 凭证，抓取成绩汇总（以及可选的明细），并返回 JSON。
    请求体: { "username": "...", "password": "..." }
    返回: { success, data: [...], message }
    """
    try:
        payload = request.get_json(silent=True) or {}
        username = (payload.get('username') or '').strip()
        password = (payload.get('password') or '').strip()

        if not username or not password:
            return jsonify({
                'success': False,
                'message': '请提供账号与密码'
            }), 400


        async def run():
            return await get_ucd_all_results(username=username,
                                         password=password)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            rows = loop.run_until_complete(run())
        finally:
            loop.close()

        # 统一返回字段，特别是把 resultsUrl -> results_url 以匹配前端
        def normalize_row(r):
            return {
                'term'        : r.get('term', ''),
                'stage'       : r.get('stage', ''),
                'year'        : r.get('year', ''),
                'programme'   : r.get('programme', ''),
                'major'       : r.get('major', ''),
                'results_url' : r.get('results_url') or r.get('resultsUrl') or ''
            }

        data = [normalize_row(r) for r in (rows or [])]

        return jsonify({
            'success': True,
            'data': data,
            'message': f'成功获取 {len(data)} 条成绩记录',
            'all': rows
        })

    except Exception as e:
        logger.exception('获取UCD成绩失败')
        return jsonify({
            'success': False,
            'message': '获取成绩数据失败',
            'error': str(e)
        }), 500


@ucd_bp.route('/test', methods=['GET'])
def test_connection():
    return jsonify({'success': True, 'message': 'UCD API 连接正常'})
