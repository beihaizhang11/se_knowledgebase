"""
Course model matching the database schema
"""

from app import db
from datetime import datetime
from sqlalchemy import func

from app.models.review import Review


class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, comment='课程标题')
    description = db.Column(db.Text, default=None, comment='课程描述')
    cover_images = db.Column(db.JSON, default=None, comment='封面图片列表(JSON格式)')
    stage = db.Column(db.Enum('S1', 'S2', 'S3', 'S4', name='course_stages'), 
                      nullable=False, comment='学期阶段')
    instructor_id = db.Column(db.Integer, 
                             db.ForeignKey('instructors.id', ondelete='CASCADE', onupdate='CASCADE'), 
                             nullable=False, comment='讲师ID')
    average_rating = db.Column(db.DECIMAL(3, 2), default=0.00, comment='平均评分(0.00-5.00)')
    total_reviews = db.Column(db.Integer, default=0, comment='总评价数量')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    reviews = db.relationship('Review', backref='course', lazy='dynamic', cascade='all, delete-orphan')
    
    # 添加索引
    __table_args__ = (
        db.Index('idx_stage', 'stage'),
        db.Index('idx_instructor', 'instructor_id'),
        db.Index('idx_rating', 'average_rating'),
    )
    
    def __repr__(self):
        return f'<Course {self.title}>'
    
    def update_rating_stats(self):
        """更新平均评分和评价数量"""
        # 计算平均评分
        avg_result = db.session.query(func.avg(Review.rating)).filter(
            Review.course_id == self.id,
            Review.rating.isnot(None)
        ).scalar()
        
        self.average_rating = round(float(avg_result), 2) if avg_result else 0.00
        
        # 计算总评价数
        self.total_reviews = self.reviews.count()
        
        db.session.commit()
    
    def to_dict(self, include_instructor=False, include_reviews=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cover_images': self.cover_images,
            'stage': self.stage,
            'instructor_id': self.instructor_id,
            'average_rating': float(self.average_rating) if self.average_rating else 0.0,
            'total_reviews': self.total_reviews,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_instructor and self.instructor:
            data['instructor'] = {
                'id': self.instructor.id,
                'name': self.instructor.name,
                'avatar_url': self.instructor.avatar_url,
                'bio': self.instructor.bio
            }
        
        if include_reviews:
            data['reviews'] = [review.to_dict(include_user=True) for review in self.reviews]
        
        return data
