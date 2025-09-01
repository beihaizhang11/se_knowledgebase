"""
Courses API endpoints matching the database schema
"""

from flask import jsonify, request
from sqlalchemy import or_
from app.api import api_bp
from app.models.course import Course
from app.models.instructor import Instructor
from app import db


@api_bp.route('/courses', methods=['GET'])
def get_courses():
    """获取课程列表，支持搜索、筛选和分页"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # 最大100条
        search = request.args.get('search', '').strip()
        stage = request.args.get('stage', '').strip()
        instructor_id = request.args.get('instructor_id', type=int)
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, title, rating
        order = request.args.get('order', 'desc')  # asc, desc
        
        # 构建查询
        query = Course.query
        
        # 搜索条件
        if search:
            query = query.join(Instructor).filter(
                or_(
                    Course.title.contains(search),
                    Course.description.contains(search),
                    Instructor.name.contains(search)
                )
            )
        
        # 筛选条件
        if stage and stage in ['S1', 'S2', 'S3', 'S4']:
            query = query.filter(Course.stage == stage)
        if instructor_id:
            query = query.filter(Course.instructor_id == instructor_id)
        
        # 排序
        if sort_by == 'title':
            order_by = Course.title.asc() if order == 'asc' else Course.title.desc()
        elif sort_by == 'rating':
            order_by = Course.average_rating.asc() if order == 'asc' else Course.average_rating.desc()
        else:  # created_at
            order_by = Course.created_at.asc() if order == 'asc' else Course.created_at.desc()
        
        query = query.order_by(order_by)
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        courses = pagination.items
        
        return jsonify({
            'success': True,
            'data': [course.to_dict(include_instructor=True) for course in courses],
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
            'message': f'获取课程列表失败: {str(e)}'
        }), 500


@api_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """获取单个课程详情"""
    try:
        course = Course.query.get_or_404(course_id)
        
        return jsonify({
            'success': True,
            'data': course.to_dict(include_instructor=True, include_reviews=True)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取课程失败: {str(e)}'
        }), 404


@api_bp.route('/courses', methods=['POST'])
def create_course():
    """创建新课程"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'stage', 'instructor_id']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} 不能为空'
                }), 400
        
        # 验证stage值
        if data['stage'] not in ['S1', 'S2', 'S3', 'S4']:
            return jsonify({
                'success': False,
                'message': 'stage必须是S1、S2、S3或S4之一'
            }), 400
        
        # 验证讲师是否存在
        instructor = Instructor.query.get(data['instructor_id'])
        if not instructor:
            return jsonify({
                'success': False,
                'message': '指定的讲师不存在'
            }), 400
        
        # 创建新课程
        course = Course(
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            cover_images=data.get('cover_images'),
            stage=data['stage'],
            instructor_id=data['instructor_id']
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '课程创建成功',
            'data': course.to_dict(include_instructor=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建课程失败: {str(e)}'
        }), 500


@api_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """更新课程"""
    try:
        course = Course.query.get_or_404(course_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供更新数据'
            }), 400
        
        # 更新字段
        if 'title' in data and data['title'].strip():
            course.title = data['title'].strip()
        if 'description' in data:
            course.description = data['description'].strip() or None
        if 'cover_images' in data:
            course.cover_images = data['cover_images']
        if 'stage' in data:
            if data['stage'] not in ['S1', 'S2', 'S3', 'S4']:
                return jsonify({
                    'success': False,
                    'message': 'stage必须是S1、S2、S3或S4之一'
                }), 400
            course.stage = data['stage']
        
        # 验证并更新讲师
        if 'instructor_id' in data:
            instructor = Instructor.query.get(data['instructor_id'])
            if not instructor:
                return jsonify({
                    'success': False,
                    'message': '指定的讲师不存在'
                }), 400
            course.instructor_id = data['instructor_id']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '课程更新成功',
            'data': course.to_dict(include_instructor=True)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新课程失败: {str(e)}'
        }), 500


@api_bp.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程"""
    try:
        course = Course.query.get_or_404(course_id)
        
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '课程删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除课程失败: {str(e)}'
        }), 500


@api_bp.route('/courses/by-stage/<stage>', methods=['GET'])
def get_courses_by_stage(stage):
    """按学期阶段获取课程"""
    try:
        if stage not in ['S1', 'S2', 'S3', 'S4']:
            return jsonify({
                'success': False,
                'message': 'stage必须是S1、S2、S3或S4之一'
            }), 400
        
        courses = Course.query.filter_by(stage=stage).order_by(Course.title).all()
        
        return jsonify({
            'success': True,
            'data': [course.to_dict(include_instructor=True) for course in courses],
            'count': len(courses),
            'stage': stage
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取课程失败: {str(e)}'
        }), 500


@api_bp.route('/courses/search', methods=['GET'])
def search_courses():
    """搜索课程"""
    try:
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            return jsonify({
                'success': False,
                'message': '搜索关键词不能为空'
            }), 400
        
        # 在标题、描述、讲师姓名中搜索
        courses = Course.query.join(Instructor).filter(
            or_(
                Course.title.contains(query_text),
                Course.description.contains(query_text),
                Instructor.name.contains(query_text)
            )
        ).order_by(Course.average_rating.desc()).limit(20).all()
        
        return jsonify({
            'success': True,
            'data': [course.to_dict(include_instructor=True) for course in courses],
            'count': len(courses),
            'query': query_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500


@api_bp.route('/courses/stats', methods=['GET'])
def get_course_stats():
    """获取课程统计信息"""
    try:
        total_courses = Course.query.count()
        
        # 按阶段统计
        stage_stats = db.session.query(
            Course.stage,
            db.func.count(Course.id).label('count')
        ).group_by(Course.stage).all()
        
        # 按讲师统计
        instructor_stats = db.session.query(
            Instructor.name,
            db.func.count(Course.id).label('count')
        ).join(Course).group_by(Instructor.id, Instructor.name).all()
        
        return jsonify({
            'success': True,
            'data': {
                'total_courses': total_courses,
                'by_stage': [
                    {'stage': stage, 'count': count}
                    for stage, count in stage_stats
                ],
                'by_instructor': [
                    {'instructor': name, 'count': count}
                    for name, count in instructor_stats
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500
