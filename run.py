"""
BDIC-SE Knowledge Base Portal
应用入口文件
"""

from app import create_app, db
from app.models import Instructor, Course, User, Review
import os

# 创建Flask应用实例
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """为Flask shell提供上下文"""
    return {
        'db': db,
        'Instructor': Instructor,
        'Course': Course,
        'User': User,
        'Review': Review
    }

@app.cli.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    print("数据库初始化完成！")

@app.cli.command()
def reset_db():
    """重置数据库（仅用于开发环境）"""
    if app.config.get('ENV') == 'production':
        print("生产环境不允许重置数据库！")
        return
    
    print("警告：此操作将删除所有数据！")
    confirm = input("确认要重置数据库吗？(yes/no): ")
    if confirm.lower() == 'yes':
        db.drop_all()
        db.create_all()
        print("数据库重置完成！请使用MySQL脚本重新导入数据。")

if __name__ == '__main__':
    # 开发环境配置
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 启动 BDIC-SE Knowledge Base Portal")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"🔧 调试模式: {'开启' if debug_mode else '关闭'}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
