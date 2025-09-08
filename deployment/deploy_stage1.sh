#!/bin/bash
# 阿里云服务器部署脚本 - SE Knowledge Base
# 服务器IP: 47.93.132.181

set -e  # 遇到错误立即退出

echo "========================================"
echo "开始部署 SE Knowledge Base 到阿里云服务器"
echo "========================================"

# 1. 更新系统
echo "1. 更新系统包..."
yum update -y

# 2. 安装必要软件
echo "2. 安装基础软件..."
yum install -y epel-release
yum install -y python3 python3-pip git nginx mysql-server mysql-devel gcc python3-devel

# 启动MySQL服务
systemctl start mysqld
systemctl enable mysqld

# 3. 安装Python虚拟环境
echo "3. 安装Python虚拟环境..."
pip3 install virtualenv

# 4. 创建项目目录
echo "4. 创建项目目录..."
mkdir -p /var/www/se_knowledgebase
cd /var/www/se_knowledgebase

# 5. 克隆项目代码
echo "5. 下载项目代码..."
git clone https://github.com/beihaizhang11/se_knowledgebase.git .

# 6. 创建Python虚拟环境
echo "6. 设置Python环境..."
python3 -m venv venv
source venv/bin/activate

# 7. 安装Python依赖
echo "7. 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 8. 配置MySQL数据库
echo "8. 配置数据库..."
# 获取MySQL临时密码
TEMP_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | awk '{print $NF}')
echo "MySQL临时密码: $TEMP_PASSWORD"

# 提示用户手动配置数据库
echo "请手动执行以下MySQL配置："
echo "mysql -u root -p"
echo "输入临时密码: $TEMP_PASSWORD"
echo "然后执行："
echo "ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';"
echo "CREATE DATABASE bdic_se_kb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "CREATE USER 'se_user'@'localhost' IDENTIFIED BY 'SeUserPassword123!';"
echo "GRANT ALL PRIVILEGES ON bdic_se_kb.* TO 'se_user'@'localhost';"
echo "FLUSH PRIVILEGES;"
echo "EXIT;"

echo "脚本第一阶段完成！请先配置数据库，然后运行第二阶段脚本。"
