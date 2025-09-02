from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(150), unique=True, nullable=False, comment='邮箱')
    password_hash = db.Column(db.String(255), nullable=False, comment='加密后的密码')
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    reviews = db.relationship('Review', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # 添加索引
    __table_args__ = (
        db.Index('idx_username', 'username'),
        db.Index('idx_email', 'email'),
    )
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Flask-Login 要求的方法"""
        return str(self.id)
    
    def get_reviews(self):
        """获取用户的所有评价"""
        return self.reviews.all()
    
    def get_reviews_count(self):
        """获取用户评价总数"""
        return self.reviews.count()
    
    def get_average_rating_given(self):
        """获取用户给出的平均评分"""
        from app.models.review import Review
        avg_result = db.session.query(func.avg(Review.rating)).filter(
            Review.user_id == self.id,
            Review.rating.isnot(None)
        ).scalar()
        return round(float(avg_result), 2) if avg_result else 0.0
    
    def get_recent_reviews(self, limit=5):
        """获取用户最近的评价"""
        from app.models.review import Review
        return Review.query.filter(Review.user_id == self.id).order_by(Review.created_at.desc()).limit(limit).all()
    
    def get_stats(self):
        """获取用户统计信息"""
        from app.models.review import Review
        
        # 获取评价统计
        total_reviews = self.reviews.count()
        
        # 获取平均评分
        avg_rating = db.session.query(func.avg(Review.rating)).filter(
            Review.user_id == self.id,
            Review.rating.isnot(None)
        ).scalar()
        avg_rating = round(float(avg_rating), 2) if avg_rating else 0.0
        
        # 获取各维度平均分
        avg_learning_gain = db.session.query(func.avg(Review.learning_gain)).filter(
            Review.user_id == self.id,
            Review.learning_gain.isnot(None)
        ).scalar()
        avg_learning_gain = round(float(avg_learning_gain), 2) if avg_learning_gain else 0.0
        
        avg_workload = db.session.query(func.avg(Review.workload)).filter(
            Review.user_id == self.id,
            Review.workload.isnot(None)
        ).scalar()
        avg_workload = round(float(avg_workload), 2) if avg_workload else 0.0
        
        avg_difficulty = db.session.query(func.avg(Review.difficulty)).filter(
            Review.user_id == self.id,
            Review.difficulty.isnot(None)
        ).scalar()
        avg_difficulty = round(float(avg_difficulty), 2) if avg_difficulty else 0.0
        
        return {
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
            'avg_learning_gain': avg_learning_gain,
            'avg_workload': avg_workload,
            'avg_difficulty': avg_difficulty
        }
    
    def update_updated_at(self):
        """更新最后修改时间"""
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'