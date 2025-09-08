#!/bin/bash
# 阿里云服务器部署脚本 第二阶段 - SE Knowledge Base
# 在完成数据库配置后运行此脚本

set -e

echo "========================================"
echo "SE Knowledge Base 部署 - 第二阶段"
echo "========================================"

cd /var/www/se_knowledgebase

# 1. 创建环境配置文件
echo "1. 创建环境配置文件..."
cat > .env << 'EOF'
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-change-this-to-random-string
JWT_SECRET_KEY=your-jwt-secret-key-change-this-to-random-string
DATABASE_URL=mysql+pymysql://se_user:SeUserPassword123!@localhost/bdic_se_kb
FLASK_DEBUG=False
EOF

# 设置文件权限
chmod 600 .env

# 2. 导入数据库结构
echo "2. 导入数据库结构..."
source venv/bin/activate
mysql -u se_user -p bdic_se_kb < database_schema.sql

# 如果有初始数据，也导入
if [ -f "DB_4_mysql5.sql" ]; then
    mysql -u se_user -p bdic_se_kb < DB_4_mysql5.sql
fi

# 3. 测试Flask应用
echo "3. 测试Flask应用..."
python run.py &
FLASK_PID=$!
sleep 5
if curl -f http://localhost:5000 > /dev/null 2>&1; then
    echo "Flask应用启动成功！"
    kill $FLASK_PID
else
    echo "Flask应用启动失败，请检查日志"
    kill $FLASK_PID
    exit 1
fi

# 4. 创建Gunicorn配置
echo "4. 配置Gunicorn..."
cat > gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 2
preload_app = True
max_requests = 1000
max_requests_jitter = 100
EOF

# 5. 创建systemd服务
echo "5. 创建系统服务..."
cat > /etc/systemd/system/se-knowledgebase.service << 'EOF'
[Unit]
Description=SE Knowledge Base Flask Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/se_knowledgebase
Environment="PATH=/var/www/se_knowledgebase/venv/bin"
ExecStart=/var/www/se_knowledgebase/venv/bin/gunicorn -c gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable se-knowledgebase
systemctl start se-knowledgebase

# 6. 配置Nginx
echo "6. 配置Nginx..."
# 停止现有的Apache/httpd服务（WordPress默认使用）
systemctl stop httpd || true
systemctl disable httpd || true

# 配置Nginx
cat > /etc/nginx/conf.d/se-knowledgebase.conf << 'EOF'
server {
    listen 80;
    server_name 47.93.132.181;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/se_knowledgebase/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
    
    access_log /var/log/nginx/se_knowledgebase_access.log;
    error_log /var/log/nginx/se_knowledgebase_error.log;
}
EOF

# 启动Nginx
systemctl start nginx
systemctl enable nginx

# 7. 配置防火墙
echo "7. 配置防火墙..."
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

echo "========================================"
echo "部署完成！"
echo "您的网站现在可以通过以下地址访问："
echo "http://47.93.132.181"
echo "========================================"
echo ""
echo "查看服务状态："
echo "systemctl status se-knowledgebase"
echo ""
echo "查看日志："
echo "journalctl -u se-knowledgebase -f"
echo ""
echo "重启服务："
echo "systemctl restart se-knowledgebase"
