"""
Instructor model matching the database schema
"""

from app import db
from datetime import datetime


class Instructor(db.Model):
    """讲师模型"""
    __tablename__ = 'instructors'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='讲师姓名')
    avatar_url = db.Column(db.String(500), default=None, comment='讲师头像图片链接')
    bio = db.Column(db.Text, default=None, comment='讲师简介')
    email = db.Column(db.String(150), default=None, comment='邮箱')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 与课程的关系
    courses = db.relationship('Course', backref='instructor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Instructor {self.name}>'
    
    def to_dict(self, include_courses=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_courses:
            data['courses'] = [course.to_dict() for course in self.courses]
            data['course_count'] = self.courses.count()
        
        return data
