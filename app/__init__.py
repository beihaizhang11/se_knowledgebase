"""
BDIC-SE Knowledge Base Portal - Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_login import LoginManager

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
login_manager = LoginManager()


def create_app(config_name='development'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from app.config import config
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    jwt.init_app(app)
    
    # 配置Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # 注册蓝图
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 添加Web页面路由
    @app.route('/')
    def index():
        """首页"""
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/courses')
    def courses_list():
        """课程列表页面"""
        from flask import render_template
        return render_template('courses_list.html')
    
    @app.route('/courses/<int:course_id>')
    def course_detail(course_id):
        """课程详情页面"""
        from flask import render_template, abort
        from app.models.course import Course
        
        course = Course.query.get_or_404(course_id)
        instructor = course.instructor
        
        return render_template('course_detail.html', course=course, instructor=instructor)
    
    @app.route('/instructors')
    def instructors_list():
        """教师列表页面"""
        from flask import render_template
        return render_template('instructors_list.html')
    
    @app.route('/instructors/<int:instructor_id>')
    def instructor_detail(instructor_id):
        """教师详情页面"""
        from flask import render_template
        from app.models.instructor import Instructor
        
        instructor = Instructor.query.get_or_404(instructor_id)
        return render_template('instructor_detail.html', instructor=instructor)
    
    @app.route('/search')
    def search():
        """搜索页面"""
        from flask import render_template, request
        query = request.args.get('q', '')
        return render_template('search_results.html', query=query)
    

    
    @app.route('/api/v1/')
    def api_info():
        """API版本信息"""
        from flask import jsonify
        return jsonify({
            "api_version": "v1",
            "status": "运行中",
            "endpoints": [
                "GET /api/v1/courses - 获取课程列表",
                "GET /api/v1/courses/<id> - 获取单个课程",
                "GET /api/v1/instructors - 获取教师列表", 
                "GET /api/v1/instructors/<id> - 获取单个教师",
                "GET /api/v1/users - 获取用户列表",
                "GET /api/v1/reviews - 获取评论列表"
            ]
        })
    
    # 注册自定义过滤器
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """将换行符转换为HTML的<br>标签"""
        if not text:
            return ''
        from markupsafe import Markup
        return Markup(str(text).replace('\n', '<br>\n'))
    
    # 注册错误处理器
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app
