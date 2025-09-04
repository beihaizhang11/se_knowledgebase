from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            user.update_updated_at()
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(next_page)
        else:
            flash('用户名/邮箱或密码错误。', 'error')
    
    return render_template('auth/login.html', title='登录', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        ucd_id = (form.ucd_student_id.data or '').strip() or None

        if ucd_id:
            exists = User.query.filter_by(ucd_student_id=ucd_id).first()
            if exists:
                flash('该 UCD 学号已被其它账号绑定', 'error')
                return render_template('auth/register.html', form=form)


        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            ucd_student_id=ucd_id
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('注册成功！请登录。', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请检查信息后重试。', 'error')
    
    return render_template('auth/register.html', title='注册', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    # 
    """用户个人资料"""
    return render_template('auth/profile.html', title='个人资料', user=current_user)

@auth_bp.route('/api/check-auth')
def check_auth():
    """检查认证状态的API端点"""
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user': current_user.to_dict() if current_user.is_authenticated else None
    })

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API登录端点"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter(
        (User.username == data['username']) | 
        (User.email == data['username'])
    ).first()
    
    if user and user.check_password(data['password']):
        login_user(user, remember=data.get('remember', False))
        user.update_updated_at()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': user.to_dict()
        })
    else:
        return jsonify({'error': '用户名/邮箱或密码错误'}), 401

@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    """API注册端点"""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} 不能为空'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '邮箱已被注册'}), 400
    
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败，请稍后重试'}), 500

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """API登出端点"""
    logout_user()
    return jsonify({'success': True, 'message': '登出成功'})
