"""
Instructors API endpoints
"""

from flask import jsonify, request
from app.api import api_bp
from app.models.instructor import Instructor
from app.models.course import Course
from app import db


@api_bp.route('/instructors', methods=['GET'])
def get_instructors():
    """获取所有讲师"""
    try:
        instructors = Instructor.query.all()
        return jsonify({
            'success': True,
            'data': [instructor.to_dict() for instructor in instructors],
            'count': len(instructors)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取讲师列表失败: {str(e)}'
        }), 500


@api_bp.route('/instructors/<int:instructor_id>', methods=['GET'])
def get_instructor(instructor_id):
    """获取单个讲师详情"""
    try:
        instructor = Instructor.query.get_or_404(instructor_id)
        return jsonify({
            'success': True,
            'data': instructor.to_dict(include_courses=True)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取讲师失败: {str(e)}'
        }), 404


@api_bp.route('/instructors', methods=['POST'])
def create_instructor():
    """创建新讲师"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'message': '讲师姓名不能为空'
            }), 400
        
        # 创建新讲师
        instructor = Instructor(
            name=data['name'].strip(),
            avatar_url=data.get('avatar_url', '').strip(),
            bio=data.get('bio', '').strip(),
            email=data.get('email', '').strip()
        )
        
        db.session.add(instructor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '讲师创建成功',
            'data': instructor.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建讲师失败: {str(e)}'
        }), 500


@api_bp.route('/instructors/<int:instructor_id>', methods=['PUT'])
def update_instructor(instructor_id):
    """更新讲师信息"""
    try:
        instructor = Instructor.query.get_or_404(instructor_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请提供更新数据'
            }), 400
        
        # 更新字段
        if 'name' in data and data['name'].strip():
            instructor.name = data['name'].strip()
        if 'avatar_url' in data:
            instructor.avatar_url = data['avatar_url'].strip()
        if 'bio' in data:
            instructor.bio = data['bio'].strip()
        if 'email' in data:
            instructor.email = data['email'].strip()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '讲师信息更新成功',
            'data': instructor.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新讲师失败: {str(e)}'
        }), 500


@api_bp.route('/instructors/<int:instructor_id>', methods=['DELETE'])
def delete_instructor(instructor_id):
    """删除讲师"""
    try:
        instructor = Instructor.query.get_or_404(instructor_id)
        
        # 检查是否有课程关联
        if instructor.courses.count() > 0:
            return jsonify({
                'success': False,
                'message': f'无法删除讲师，还有 {instructor.courses.count()} 门课程关联此讲师'
            }), 400
        
        db.session.delete(instructor)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '讲师删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除讲师失败: {str(e)}'
        }), 500


@api_bp.route('/instructors/<int:instructor_id>/courses', methods=['GET'])
def get_instructor_courses(instructor_id):
    """获取指定讲师的课程列表"""
    try:
        instructor = Instructor.query.get_or_404(instructor_id)
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        
        # 查询讲师的课程
        courses_query = Course.query.filter_by(instructor_id=instructor_id)
        
        # 执行分页查询
        pagination = courses_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        courses = [course.to_dict() for course in pagination.items]
        
        return jsonify({
            'success': True,
            'data': courses,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取讲师课程失败: {str(e)}'
        }), 500
