"""
API Blueprint for BDIC-SE Knowledge Base Portal
"""

from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入路由
from app.api import courses, instructors, reviews, users

__all__ = ['api_bp']
