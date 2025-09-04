from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(150), unique=True, nullable=False, comment='邮箱')
    ucd_student_id = db.Column(db.String(64), unique=True, nullable=True)  # 学号/用户名
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
    
    def __init__(self, username, email, password, ucd_student_id=None):
        self.username = username
        self.email = email
        self.ucd_student_id = ucd_student_id
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
    
    def get_full_name(self):
        """获取用户全名，如果没有名字则返回用户名"""
        return self.username
    
    def get_initials(self):
        """获取用户名首字母"""
        if len(self.username) >= 2:
            return self.username[:2].upper()
        return self.username[0].upper() if self.username else "U"
    
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
            'ucd_student_id': self.ucd_student_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'