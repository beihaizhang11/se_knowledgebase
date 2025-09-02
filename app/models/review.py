"""
Review model matching the database schema
"""

from app import db
from datetime import datetime


class Review(db.Model):
    """评价模型（合并评分和评论）"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), 
                        nullable=False, comment='用户ID')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE', onupdate='CASCADE'), 
                         nullable=False, comment='课程ID')
    rating = db.Column(db.SmallInteger, default=None, comment='评分(1-5分)')
    learning_gain = db.Column(db.SmallInteger, default=None, comment='课程收获评分(1-5分)')
    workload = db.Column(db.SmallInteger, default=None, comment='繁忙程度评分(1-5分,1=轻松,5=繁忙)')
    difficulty = db.Column(db.SmallInteger, default=None, comment='课程难度评分(1-5分,1=简单,5=困难)')
    content = db.Column(db.Text, default=None, comment='评论内容')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 添加检查约束
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        db.CheckConstraint('learning_gain >= 1 AND learning_gain <= 5', name='check_learning_gain_range'),
        db.CheckConstraint('workload >= 1 AND workload <= 5', name='check_workload_range'),
        db.CheckConstraint('difficulty >= 1 AND difficulty <= 5', name='check_difficulty_range'),
        db.UniqueConstraint('user_id', 'course_id', name='unique_user_course'),
        db.Index('idx_course', 'course_id'),
        db.Index('idx_rating', 'rating'),
        db.Index('idx_learning_gain', 'learning_gain'),
        db.Index('idx_workload', 'workload'),
        db.Index('idx_difficulty', 'difficulty'),
        db.Index('idx_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Review {self.user.username if self.user else "Unknown"} -> {self.course.title if self.course else "Unknown"}: {self.rating}/5>'
    
    def to_dict(self, include_user=False, include_course=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'rating': self.rating,
            'learning_gain': self.learning_gain,
            'workload': self.workload,
            'difficulty': self.difficulty,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username
            }
        
        if include_course and self.course:
            data['course'] = {
                'id': self.course.id,
                'title': self.course.title
            }
        
        return data
