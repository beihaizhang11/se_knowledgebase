"""
Error handlers for the Flask application
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': '请求的资源不存在',
            'status_code': 404
        }), 404
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'error': 'Bad Request',
            'message': '请求参数错误',
            'status_code': 400
        }), 400
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误',
            'status_code': 500
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        """处理所有HTTP异常"""
        return jsonify({
            'error': e.name,
            'message': e.description,
            'status_code': e.code
        }), e.code
