# SE Knowledge Base 阿里云部署完整指南

## 服务器信息
- **公网IP**: 47.93.132.181
- **实例名称**: WordPress-xguc
- **地域**: 华北2（北京）
- **到期时间**: 2026年1月25日

## 部署步骤

### 第一步：连接服务器

1. **重置服务器密码**：
   - 登录阿里云ECS控制台
   - 选择实例 "WordPress-xguc"
   - 点击"更多" → "密码/密钥" → "重置实例密码"
   - 设置一个强密码（至少8位，包含大小写字母、数字和特殊字符）
   - 重启实例

2. **SSH连接服务器**：
   ```bash
   ssh root@47.93.132.181
   ```

### 第二步：运行部署脚本

1. **下载并运行第一阶段部署脚本**：
   ```bash
   # 下载部署脚本
   curl -O https://raw.githubusercontent.com/beihaizhang11/se_knowledgebase/main/deployment/deploy_stage1.sh
   
   # 给脚本执行权限
   chmod +x deploy_stage1.sh
   
   # 运行第一阶段
   ./deploy_stage1.sh
   ```

2. **配置MySQL数据库**：
   脚本会显示MySQL临时密码，请记录下来，然后执行：
   ```bash
   mysql -u root -p
   # 输入临时密码
   
   # 设置新的root密码
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';
   
   # 创建数据库和用户
   CREATE DATABASE bdic_se_kb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'se_user'@'localhost' IDENTIFIED BY 'SeUserPassword123!';
   GRANT ALL PRIVILEGES ON bdic_se_kb.* TO 'se_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

3. **运行第二阶段部署脚本**：
   ```bash
   # 下载第二阶段脚本
   curl -O https://raw.githubusercontent.com/beihaizhang11/se_knowledgebase/main/deployment/deploy_stage2.sh
   
   # 给脚本执行权限
   chmod +x deploy_stage2.sh
   
   # 运行第二阶段
   ./deploy_stage2.sh
   ```

### 第三步：验证部署

1. **检查服务状态**：
   ```bash
   # 检查Flask应用状态
   systemctl status se-knowledgebase
   
   # 检查Nginx状态
   systemctl status nginx
   
   # 检查MySQL状态
   systemctl status mysqld
   ```

2. **访问网站**：
   在浏览器中访问：`http://47.93.132.181`

### 第四步：安全配置

1. **修改安全密钥**（重要）：
   ```bash
   cd /var/www/se_knowledgebase
   
   # 编辑环境文件
   vim .env
   
   # 修改以下内容为随机字符串：
   SECRET_KEY=生成一个随机的32位字符串
   JWT_SECRET_KEY=生成另一个随机的32位字符串
   ```

2. **配置防火墙**：
   ```bash
   # 只开放必要端口
   firewall-cmd --permanent --remove-service=ssh  # 如果使用密钥登录
   firewall-cmd --permanent --add-port=22/tcp     # SSH端口
   firewall-cmd --permanent --add-service=http
   firewall-cmd --permanent --add-service=https
   firewall-cmd --reload
   ```

## 常用管理命令

### 服务管理
```bash
# 重启应用
systemctl restart se-knowledgebase

# 查看应用日志
journalctl -u se-knowledgebase -f

# 重启Nginx
systemctl restart nginx

# 查看Nginx日志
tail -f /var/log/nginx/se_knowledgebase_error.log
```

### 代码更新
```bash
cd /var/www/se_knowledgebase
git pull origin main
systemctl restart se-knowledgebase
```

### 数据库备份
```bash
# 备份数据库
mysqldump -u se_user -p bdic_se_kb > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
mysql -u se_user -p bdic_se_kb < backup_file.sql
```

## 故障排除

### 应用无法启动
```bash
# 查看详细错误日志
journalctl -u se-knowledgebase -n 50

# 检查Python环境
cd /var/www/se_knowledgebase
source venv/bin/activate
python run.py
```

### 无法访问网站
```bash
# 检查Nginx配置
nginx -t

# 检查端口占用
netstat -tlnp | grep :80

# 检查防火墙
firewall-cmd --list-all
```

### 数据库连接问题
```bash
# 测试数据库连接
mysql -u se_user -p -h localhost bdic_se_kb

# 检查MySQL服务
systemctl status mysqld
```

## 性能优化建议

1. **增加Gunicorn workers**：
   编辑 `gunicorn.conf.py`，增加workers数量

2. **配置SSL证书**（如果有域名）：
   ```bash
   yum install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

3. **设置定时备份**：
   ```bash
   crontab -e
   # 添加每日备份
   0 2 * * * mysqldump -u se_user -pSeUserPassword123! bdic_se_kb > /backup/db_$(date +\%Y\%m\%d).sql
   ```

## 联系信息
如果部署过程中遇到问题，请检查：
1. 服务器日志：`journalctl -u se-knowledgebase -f`
2. Nginx日志：`/var/log/nginx/se_knowledgebase_error.log`
3. 数据库连接配置：`.env` 文件中的数据库连接字符串

部署完成后，您的知识库网站将在 `http://47.93.132.181` 上运行！
