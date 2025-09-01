"""
Users API endpoints matching the database schema
"""

from flask import jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from app.api import api_bp
from app.models.user import User
from app.models.review import Review
from app import db
import re


def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """验证密码强度（至少6位，包含字母和数字）"""
    if len(password) < 6:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


@api_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表，支持搜索和分页"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # 最大100条
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, username, email
        order = request.args.get('order', 'desc')  # asc, desc
        
        # 构建查询
        query = User.query
        
        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )
        
        # 排序
        if sort_by == 'username':
            order_by = User.username.asc() if order == 'asc' else User.username.desc()
        elif sort_by == 'email':
            order_by = User.email.asc() if order == 'asc' else User.email.desc()
        else:  # created_at
            order_by = User.created_at.asc() if order == 'asc' else User.created_at.desc()
        
        query = query.order_by(order_by)
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = pagination.items
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取单个用户详情"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 获取用户的评价统计
        review_stats = db.session.query(
            db.func.count(Review.id).label('total_reviews'),
            db.func.avg(Review.rating).label('avg_rating_given')
        ).filter_by(user_id=user_id).first()
        
        user_data = user.to_dict(include_reviews=True)
        user_data['statistics'] = {
            'total_reviews': review_stats.total_reviews or 0,
            'avg_rating_given': round(float(review_stats.avg_rating_given), 1) if review_stats.avg_rating_given else 0.0
        }
        
        return jsonify({
            'success': True,
            'data': user_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户失败: {str(e)}'
        }), 404


@api_bp.route('/users', methods=['POST'])
def create_user():
    """创建新用户（注册）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data or field not in data or not data[field].strip():
                return jsonify({
                    'success': False,
                    'message': f'{field} 不能为空'
                }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # 验证用户名长度
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'success': False,
                'message': '用户名长度必须在3-50个字符之间'
            }), 400
        
        # 验证邮箱格式
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        # 验证密码强度
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': '密码至少6位，必须包含字母和数字'
            }), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': '邮箱已存在'
            }), 400
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户注册成功',
            'data': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供更新数据'
            }), 400
        
        # 更新用户名
        if 'username' in data:
            new_username = data['username'].strip()
            if not new_username:
                return jsonify({
                    'success': False,
                    'message': '用户名不能为空'
                }), 400
            
            if len(new_username) < 3 or len(new_username) > 50:
                return jsonify({
                    'success': False,
                    'message': '用户名长度必须在3-50个字符之间'
                }), 400
            
            # 检查用户名是否已被其他用户使用
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({
                    'success': False,
                    'message': '用户名已存在'
                }), 400
            
            user.username = new_username
        
        # 更新邮箱
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if not new_email:
                return jsonify({
                    'success': False,
                    'message': '邮箱不能为空'
                }), 400
            
            if not validate_email(new_email):
                return jsonify({
                    'success': False,
                    'message': '邮箱格式不正确'
                }), 400
            
            # 检查邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({
                    'success': False,
                    'message': '邮箱已存在'
                }), 400
            
            user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>/change-password', methods=['PUT'])
def change_password(user_id):
    """修改用户密码"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供密码数据'
            }), 400
        
        # 验证必填字段
        if 'old_password' not in data or 'new_password' not in data:
            return jsonify({
                'success': False,
                'message': '请提供旧密码和新密码'
            }), 400
        
        old_password = data['old_password']
        new_password = data['new_password']
        
        # 验证旧密码
        if not check_password_hash(user.password_hash, old_password):
            return jsonify({
                'success': False,
                'message': '旧密码不正确'
            }), 400
        
        # 验证新密码强度
        if not validate_password(new_password):
            return jsonify({
                'success': False,
                'message': '新密码至少6位，必须包含字母和数字'
            }), 400
        
        # 检查新密码与旧密码是否相同
        if check_password_hash(user.password_hash, new_password):
            return jsonify({
                'success': False,
                'message': '新密码不能与旧密码相同'
            }), 400
        
        # 更新密码
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'修改密码失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 检查用户是否有评价
        review_count = user.reviews.count()
        if review_count > 0:
            return jsonify({
                'success': False,
                'message': f'无法删除用户，还有 {review_count} 条评价关联此用户'
            }), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': '请提供邮箱和密码'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # 查找用户
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({
                'success': False,
                'message': '邮箱或密码错误'
            }), 401
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500


@api_bp.route('/users/check-username/<username>', methods=['GET'])
def check_username(username):
    """检查用户名是否可用"""
    try:
        username = username.strip()
        
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                'success': False,
                'available': False,
                'message': '用户名长度必须在3-50个字符之间'
            })
        
        existing_user = User.query.filter_by(username=username).first()
        
        return jsonify({
            'success': True,
            'available': existing_user is None,
            'message': '用户名可用' if existing_user is None else '用户名已存在'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查用户名失败: {str(e)}'
        }), 500


@api_bp.route('/users/check-email/<email>', methods=['GET'])
def check_email(email):
    """检查邮箱是否可用"""
    try:
        email = email.strip().lower()
        
        if not validate_email(email):
            return jsonify({
                'success': False,
                'available': False,
                'message': '邮箱格式不正确'
            })
        
        existing_user = User.query.filter_by(email=email).first()
        
        return jsonify({
            'success': True,
            'available': existing_user is None,
            'message': '邮箱可用' if existing_user is None else '邮箱已存在'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查邮箱失败: {str(e)}'
        }), 500


@api_bp.route('/users/stats', methods=['GET'])
def get_user_stats():
    """获取用户统计信息"""
    try:
        total_users = User.query.count()
        
        # 最活跃用户（评价最多）
        active_users = db.session.query(
            User.username,
            db.func.count(Review.id).label('review_count')
        ).join(Review).group_by(User.id, User.username)\
         .order_by(db.func.count(Review.id).desc()).limit(10).all()
        
        # 新注册用户（最近7天）
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_count = User.query.filter(User.created_at >= week_ago).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_users': total_users,
                'new_users_this_week': new_users_count,
                'most_active_users': [
                    {'username': username, 'review_count': count}
                    for username, count in active_users
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户统计失败: {str(e)}'
        }), 500
