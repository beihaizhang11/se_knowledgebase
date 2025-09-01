from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models.user import User

class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名/邮箱', validators=[
        DataRequired(message='请输入用户名或邮箱'),
        Length(min=3, max=80, message='用户名长度应在3-80个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码')
    ])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=50, message='用户名长度应在3-50个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, message='密码长度至少6个字符')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        """验证用户名是否已存在"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('用户名已存在，请选择其他用户名。')
    
    def validate_email(self, email):
        """验证邮箱是否已存在"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('邮箱已被注册，请使用其他邮箱。')

class ChangePasswordForm(FlaskForm):
    """修改密码表单"""
    current_password = PasswordField('当前密码', validators=[
        DataRequired(message='请输入当前密码')
    ])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, message='密码长度至少6个字符')
    ])
    new_password2 = PasswordField('确认新密码', validators=[
        DataRequired(message='请确认新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('修改密码')

class EditProfileForm(FlaskForm):
    """编辑个人资料表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=50, message='用户名长度应在3-50个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    submit = SubmitField('保存修改')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        """验证用户名是否已存在（排除当前用户）"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('用户名已存在，请选择其他用户名。')
    
    def validate_email(self, email):
        """验证邮箱是否已存在（排除当前用户）"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('邮箱已被注册，请使用其他邮箱。')
