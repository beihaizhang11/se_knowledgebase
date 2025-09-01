"""
Reviews API endpoints matching the database schema
"""

from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app.api import api_bp
from app.models.review import Review
from app.models.course import Course
from app.models.user import User
from app import db


@api_bp.route('/courses/<int:course_id>/reviews', methods=['GET'])
def get_course_reviews(course_id):
    """获取课程的所有评价"""
    try:
        # 验证课程是否存在
        course = Course.query.get_or_404(course_id)
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # 获取评价列表
        pagination = Review.query.filter_by(course_id=course_id)\
            .order_by(Review.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        reviews = pagination.items
        
        # 计算统计信息
        stats = db.session.query(
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('total_reviews'),
            func.count(Review.rating).label('rated_reviews')
        ).filter_by(course_id=course_id).first()
        
        # 评分分布
        rating_distribution = db.session.query(
            Review.rating,
            func.count(Review.id).label('count')
        ).filter(
            Review.course_id == course_id,
            Review.rating.isnot(None)
        ).group_by(Review.rating).all()
        
        return jsonify({
            'success': True,
            'data': {
                'course': course.to_dict(include_instructor=True),
                'reviews': [review.to_dict(include_user=True) for review in reviews],
                'statistics': {
                    'average_rating': round(float(stats.avg_rating), 1) if stats.avg_rating else 0.0,
                    'total_reviews': stats.total_reviews or 0,
                    'rated_reviews': stats.rated_reviews or 0
                },
                'rating_distribution': [
                    {'rating': rating, 'count': count}
                    for rating, count in rating_distribution
                ]
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取评价失败: {str(e)}'
        }), 500


@api_bp.route('/courses/<int:course_id>/reviews', methods=['POST'])
@login_required
def create_review(course_id):
    """为课程创建评价"""
    try:
        # 验证课程是否存在
        course = Course.query.get_or_404(course_id)
        
        data = request.get_json()
        
        # 使用当前登录用户的ID
        user_id = current_user.id
        
        # 检查是否已经评价过
        existing_review = Review.query.filter_by(
            course_id=course_id,
            user_id=user_id
        ).first()
        
        if existing_review:
            return jsonify({
                'success': False,
                'message': '您已经对此课程评价过了'
            }), 400
        
        # 验证评分范围（如果提供了评分）
        rating_value = data.get('rating') if data else None
        if rating_value is not None:
            if not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
                return jsonify({
                    'success': False,
                    'message': '评分必须是1-5之间的整数'
                }), 400
        
        # 创建新评价
        review = Review(
            course_id=course_id,
            user_id=user_id,
            rating=rating_value,
            content=data.get('content', '').strip() or None if data else None
        )
        
        db.session.add(review)
        db.session.commit()
        
        # 更新课程的评分统计
        course.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': '评价提交成功',
            'data': review.to_dict(include_user=True, include_course=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交评价失败: {str(e)}'
        }), 500


@api_bp.route('/reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """获取单个评价详情"""
    try:
        review = Review.query.get_or_404(review_id)
        return jsonify({
            'success': True,
            'data': review.to_dict(include_user=True, include_course=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取评价失败: {str(e)}'
        }), 404


@api_bp.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """更新评价（仅允许评价者本人更新）"""
    try:
        review = Review.query.get_or_404(review_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供更新数据'
            }), 400
        
        # 验证用户权限（简单的身份验证）
        if 'user_id' in data and data['user_id'] != review.user_id:
            return jsonify({
                'success': False,
                'message': '只能修改自己的评价'
            }), 403
        
        # 更新字段
        if 'rating' in data:
            rating_value = data['rating']
            if rating_value is not None:
                if not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
                    return jsonify({
                        'success': False,
                        'message': '评分必须是1-5之间的整数'
                    }), 400
            review.rating = rating_value
        
        if 'content' in data:
            review.content = data['content'].strip() or None
        
        db.session.commit()
        
        # 更新课程的评分统计
        review.course.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': '评价更新成功',
            'data': review.to_dict(include_user=True, include_course=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新评价失败: {str(e)}'
        }), 500


@api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """删除评价"""
    try:
        review = Review.query.get_or_404(review_id)
        course = review.course  # 保存课程引用用于更新统计
        
        db.session.delete(review)
        db.session.commit()
        
        # 更新课程的评分统计
        course.update_rating_stats()
        
        return jsonify({
            'success': True,
            'message': '评价删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除评价失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>/reviews', methods=['GET'])
def get_user_reviews(user_id):
    """获取用户的所有评价"""
    try:
        # 验证用户是否存在
        user = User.query.get_or_404(user_id)
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # 获取用户评价列表
        pagination = Review.query.filter_by(user_id=user_id)\
            .order_by(Review.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        reviews = pagination.items
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'reviews': [review.to_dict(include_course=True) for review in reviews]
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户评价失败: {str(e)}'
        }), 500


@api_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """获取评价列表，支持按课程、教师、用户筛选"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        course_id = request.args.get('course_id', type=int)
        instructor_id = request.args.get('instructor_id', type=int)
        user_id = request.args.get('user_id', type=int)
        sort_by = request.args.get('sort', 'newest')  # newest, oldest, highest, lowest
        
        # 构建查询
        query = Review.query.join(Course)
        
        # 筛选条件
        if course_id:
            query = query.filter(Review.course_id == course_id)
        if instructor_id:
            query = query.filter(Course.instructor_id == instructor_id)
        if user_id:
            query = query.filter(Review.user_id == user_id)
        
        # 排序
        if sort_by == 'oldest':
            query = query.order_by(Review.created_at.asc())
        elif sort_by == 'highest':
            query = query.order_by(Review.rating.desc().nulls_last())
        elif sort_by == 'lowest':
            query = query.order_by(Review.rating.asc().nulls_last())
        else:  # newest
            query = query.order_by(Review.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        reviews = pagination.items
        
        return jsonify({
            'success': True,
            'data': [review.to_dict(include_user=True, include_course=True) for review in reviews],
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
            'message': f'获取评价失败: {str(e)}'
        }), 500


@api_bp.route('/reviews', methods=['POST'])
def create_review_general():
    """创建评价（通用接口）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['course_id', 'user_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} 不能为空'
                }), 400
        
        # 验证课程是否存在
        course = Course.query.get(data['course_id'])
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在'
            }), 400
        
        # 验证用户是否存在
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 400
        
        # 检查是否已经评价过
        existing_review = Review.query.filter_by(
            course_id=data['course_id'],
            user_id=data['user_id']
        ).first()
        
        if existing_review:
            return jsonify({
                'success': False,
                'message': '您已经对此课程评价过了'
            }), 400
        
        # 验证评分范围（如果提供了评分）
        rating_value = data.get('rating')
        if rating_value is not None:
            if not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
                return jsonify({
                    'success': False,
                    'message': '评分必须是1-5之间的整数'
                }), 400
        
        # 创建新评价
        review = Review(
            course_id=data['course_id'],
            user_id=data['user_id'],
            rating=rating_value,
            content=data.get('content', '').strip() or None
        )
        
        db.session.add(review)
        db.session.commit()
        
        # 更新课程的评分统计
        course.update_rating_stats()
        
        return jsonify({
            'success': True,
            'data': review.to_dict(include_user=True, include_course=True),
            'message': '评价提交成功'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交评价失败: {str(e)}'
        }), 500


@api_bp.route('/reviews/check', methods=['POST'])
def check_review_eligibility():
    """检查用户是否可以对课程评价"""
    try:
        data = request.get_json()
        
        if not data or 'course_id' not in data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        course_id = data['course_id']
        user_id = data['user_id']
        
        # 验证课程和用户是否存在
        course = Course.query.get(course_id)
        user = User.query.get(user_id)
        if not course:
            return jsonify({
                'success': False,
                'message': '课程不存在'
            }), 404
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 检查是否已经评价
        existing_review = Review.query.filter_by(
            course_id=course_id,
            user_id=user_id
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'can_review': existing_review is None,
                'existing_review': existing_review.to_dict() if existing_review else None,
                'course': course.to_dict(include_instructor=True),
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查评价资格失败: {str(e)}'
        }), 500
