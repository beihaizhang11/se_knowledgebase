#!/bin/bash
# 一键部署脚本 - SE Knowledge Base
# 使用方法：curl -sSL https://raw.githubusercontent.com/beihaizhang11/se_knowledgebase/main/deployment/quick_deploy.sh | bash

set -e

echo "========================================"
echo "SE Knowledge Base 一键部署脚本"
echo "服务器IP: $(curl -s ifconfig.me)"
echo "========================================"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root用户运行此脚本"
    exit 1
fi

# 1. 更新系统
echo "1. 更新系统..."
if command -v yum &> /dev/null; then
    yum update -y
    yum install -y epel-release
    yum install -y python3 python3-pip git nginx mysql-server mysql-devel gcc python3-devel curl wget
elif command -v apt &> /dev/null; then
    apt update && apt upgrade -y
    apt install -y python3 python3-pip python3-venv git nginx mysql-server libmysqlclient-dev build-essential curl wget
fi

# 2. 启动MySQL
echo "2. 启动MySQL..."
systemctl start mysqld || systemctl start mysql
systemctl enable mysqld || systemctl enable mysql

# 3. 设置MySQL（自动化）
echo "3. 配置MySQL..."
# 生成随机密码
DB_ROOT_PASS=$(openssl rand -base64 12)
DB_USER_PASS=$(openssl rand -base64 12)

# CentOS/RHEL MySQL配置
if [ -f "/var/log/mysqld.log" ]; then
    TEMP_PASS=$(grep 'temporary password' /var/log/mysqld.log | tail -1 | awk '{print $NF}')
    mysql --connect-expired-password -u root -p$TEMP_PASS << EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$DB_ROOT_PASS';
CREATE DATABASE bdic_se_kb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'se_user'@'localhost' IDENTIFIED BY '$DB_USER_PASS';
GRANT ALL PRIVILEGES ON bdic_se_kb.* TO 'se_user'@'localhost';
FLUSH PRIVILEGES;
EOF
else
    # Ubuntu/Debian MySQL配置
    mysql -u root << EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$DB_ROOT_PASS';
CREATE DATABASE bdic_se_kb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'se_user'@'localhost' IDENTIFIED BY '$DB_USER_PASS';
GRANT ALL PRIVILEGES ON bdic_se_kb.* TO 'se_user'@'localhost';
FLUSH PRIVILEGES;
EOF
fi

# 4. 下载项目
echo "4. 下载项目..."
cd /var/www
rm -rf se_knowledgebase
git clone https://github.com/beihaizhang11/se_knowledgebase.git
cd se_knowledgebase

# 5. 设置Python环境
echo "5. 设置Python环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 6. 创建配置文件
echo "6. 创建配置文件..."
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)
DATABASE_URL=mysql+pymysql://se_user:$DB_USER_PASS@localhost/bdic_se_kb
FLASK_DEBUG=False
EOF

chmod 600 .env

# 7. 导入数据库
echo "7. 导入数据库..."
mysql -u se_user -p$DB_USER_PASS bdic_se_kb < database_schema.sql
if [ -f "DB_4_mysql5.sql" ]; then
    mysql -u se_user -p$DB_USER_PASS bdic_se_kb < DB_4_mysql5.sql
fi

# 8. 创建Gunicorn配置
echo "8. 配置应用服务..."
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

# 9. 创建systemd服务
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

systemctl daemon-reload
systemctl enable se-knowledgebase
systemctl start se-knowledgebase

# 10. 配置Nginx
echo "9. 配置Nginx..."
# 停止可能冲突的服务
systemctl stop httpd 2>/dev/null || true
systemctl disable httpd 2>/dev/null || true

# 获取服务器公网IP
PUBLIC_IP=$(curl -s ifconfig.me)

cat > /etc/nginx/conf.d/se-knowledgebase.conf << EOF
server {
    listen 80;
    server_name $PUBLIC_IP _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/se_knowledgebase/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
}
EOF

# 移除默认配置
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

systemctl start nginx
systemctl enable nginx

# 11. 配置防火墙
echo "10. 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
elif command -v ufw &> /dev/null; then
    ufw allow 80
    ufw allow 443
fi

# 12. 保存密码信息
echo "11. 保存配置信息..."
cat > /root/se_knowledgebase_info.txt << EOF
SE Knowledge Base 部署信息
========================
部署时间: $(date)
服务器IP: $PUBLIC_IP
网站访问: http://$PUBLIC_IP

数据库信息:
- 数据库名: bdic_se_kb
- 用户名: se_user
- 密码: $DB_USER_PASS
- Root密码: $DB_ROOT_PASS

项目路径: /var/www/se_knowledgebase
配置文件: /var/www/se_knowledgebase/.env

常用命令:
- 重启应用: systemctl restart se-knowledgebase
- 查看日志: journalctl -u se-knowledgebase -f
- 更新代码: cd /var/www/se_knowledgebase && git pull && systemctl restart se-knowledgebase
EOF

echo "========================================"
echo "部署完成！"
echo "========================================"
echo "网站地址: http://$PUBLIC_IP"
echo ""
echo "数据库信息已保存到: /root/se_knowledgebase_info.txt"
echo "请使用以下命令查看："
echo "cat /root/se_knowledgebase_info.txt"
echo ""
echo "检查服务状态："
echo "systemctl status se-knowledgebase"
echo "systemctl status nginx"
echo ""
echo "如有问题，查看日志："
echo "journalctl -u se-knowledgebase -f"
