from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Bill, Settlement, Receipt, SystemConfig, LoginLog
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from functools import wraps
import os
import secrets
import shutil
import tempfile

app = Flask(__name__)

# 安全的SECRET_KEY生成
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# 会话配置 - 确保每个设备独立
app.config['SESSION_COOKIE_NAME'] = 'roommate_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JS访问
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF保护
app.config['SESSION_COOKIE_SECURE'] = False  # 生产环境应设为True(HTTPS)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 7天有效期

# 强制使用项目目录内的绝对路径（解决IDE运行目录问题）
# 数据库路径 - 强制在项目目录内
INSTANCE_PATH = os.path.join(app.root_path, 'instance')
DB_PATH = os.path.join(INSTANCE_PATH, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 文件上传配置 - 使用项目目录内的绝对路径
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'receipts')
print(f"数据库路径: {DB_PATH}")
print(f"上传路径: {UPLOAD_FOLDER}")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Flask-Login配置 - 多设备支持
login_manager.remember_cookie_duration = timedelta(days=30)  # 记住我30天
login_manager.session_protection = 'strong'  # 强会话保护

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    """管理员权限检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限才能访问此页面', 'error')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_with_timestamp(filename):
    """为文件名添加时间戳以避免冲突"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{timestamp}_{name}{ext}"

def validate_password_strength(password):
    """验证密码强度"""
    import re

    errors = []

    # 从系统配置获取最小密码长度
    min_length = SystemConfig.get_config('security.password_min_length', 8)

    # 长度检查
    if len(password) < min_length:
        errors.append(f"密码至少需要{min_length}个字符")

    # 包含字母检查
    if not re.search(r'[a-zA-Z]', password):
        errors.append("密码必须包含字母")

    # 包含数字检查
    if not re.search(r'\d', password):
        errors.append("密码必须包含数字")

    # 可选：包含特殊字符（暂时不强制要求）
    # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    #     errors.append("密码必须包含特殊字符")

    return errors

def get_disk_space():
    """获取磁盘可用空间（MB）"""
    statvfs = os.statvfs(app.root_path)
    available_bytes = statvfs.f_bavail * statvfs.f_frsize
    return available_bytes / (1024 * 1024)  # 转换为MB

def check_sufficient_disk_space(required_size_mb):
    """检查磁盘空间是否足够"""
    # 获取最小空间要求配置（默认100MB）
    min_space_mb = int(os.environ.get('MIN_DISK_SPACE_MB', 100))
    available_mb = get_disk_space()

    # 需要保留最小空间 + 上传文件大小
    needed_mb = min_space_mb + required_size_mb

    return available_mb >= needed_mb, available_mb, min_space_mb

def estimate_files_size(files):
    """估算文件总大小（MB）"""
    total_size = 0
    for file in files:
        if file and hasattr(file, 'seek') and hasattr(file, 'tell'):
            # 保存当前位置
            current_pos = file.tell()
            # 移动到文件末尾
            file.seek(0, os.SEEK_END)
            size = file.tell()
            # 恢复原位置
            file.seek(current_pos)
            total_size += size
    return total_size / (1024 * 1024)  # 转换为MB

class FileUploadTransaction:
    """文件上传事务管理器"""

    def __init__(self, bill_id):
        self.bill_id = bill_id
        self.temp_dir = None
        self.uploaded_files = []
        self.database_objects = []

    def __enter__(self):
        """开始事务"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix=f'bill_{self.bill_id}_')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束事务，如果有异常则回滚"""
        if exc_type is not None:
            # 发生异常，执行回滚
            self.rollback()
        else:
            # 没有异常，提交事务
            self.commit()

        # 清理临时目录
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def save_file(self, file, filename):
        """保存文件到临时目录"""
        temp_path = os.path.join(self.temp_dir, filename)
        file.save(temp_path)
        self.uploaded_files.append((temp_path, filename))
        return temp_path

    def add_database_object(self, obj):
        """添加数据库对象到事务"""
        self.database_objects.append(obj)
        db.session.add(obj)

    def commit(self):
        """提交事务 - 移动文件到最终位置"""
        if not self.uploaded_files:
            return

        # 创建目标目录
        bill_folder = os.path.join(UPLOAD_FOLDER, str(self.bill_id))
        os.makedirs(bill_folder, exist_ok=True)

        # 移动文件到最终位置
        for temp_path, filename in self.uploaded_files:
            final_path = os.path.join(bill_folder, filename)
            shutil.move(temp_path, final_path)

    def rollback(self):
        """回滚事务 - 删除数据库对象"""
        # 回滚数据库对象
        for obj in self.database_objects:
            if obj in db.session:
                db.session.expunge(obj)

        # 临时文件会在 __exit__ 中自动清理

def log_login_attempt(username, user_id=None, success=True, failure_reason=None):
    """记录登录尝试"""
    # 获取客户端IP地址
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '未知'))
    if ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # 获取用户代理
    user_agent = request.headers.get('User-Agent', '未知')[:500]  # 限制长度

    # 创建日志记录
    login_log = LoginLog(
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )

    db.session.add(login_log)
    try:
        db.session.commit()
    except:
        db.session.rollback()

def init_database():
    """初始化数据库和默认用户"""
    # 确保必要的目录存在 - 使用明确的路径
    os.makedirs(INSTANCE_PATH, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print(f"创建目录: {INSTANCE_PATH}")
    print(f"创建目录: {app.config['UPLOAD_FOLDER']}")

    db.create_all()

    # 检查是否已有用户
    if User.query.count() == 0:
        # 创建4个室友账号
        roommates = [
            {'username': 'roommate1', 'display_name': '室友1', 'password': 'password123'},
            {'username': 'roommate2', 'display_name': '室友2', 'password': 'password123'},
            {'username': 'roommate3', 'display_name': '室友3', 'password': 'password123'},
            {'username': 'roommate4', 'display_name': '室友4', 'password': 'password123'},
        ]

        for i, roommate in enumerate(roommates):
            user = User(
                username=roommate['username'],
                display_name=roommate['display_name'],
                is_default_password=True,  # 标记为使用默认密码
                is_admin=(i == 0)  # 第一个用户为管理员
            )
            user.set_password(roommate['password'])
            db.session.add(user)

        db.session.commit()
        print("已创建默认用户账号")

    # 初始化系统配置
    if SystemConfig.query.count() == 0:
        default_configs = [
            # 安全设置
            ('security.max_login_attempts', '5', '登录失败次数限制'),
            ('security.lockout_duration_minutes', '15', '账户锁定时长（分钟）'),
            ('security.password_min_length', '8', '密码最小长度'),
            ('security.force_change_default_password', 'true', '是否强制修改默认密码'),

            # 账单设置
            ('bills.allow_delete_settled', 'false', '是否允许删除已结算的账单'),
            ('bills.max_file_size_mb', '10', '凭证文件大小限制（MB）'),
            ('bills.allowed_file_types', 'png,jpg,jpeg,gif,pdf', '允许的文件类型'),

            # 系统设置
            ('system.default_password', 'password123', '系统默认密码'),
            ('system.name', '室友记账系统', '系统名称'),
        ]

        for key, value, description in default_configs:
            SystemConfig.set_config(key, value, description)

        db.session.commit()
        print("已初始化系统配置")

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # 获取所有账单
    bills = Bill.query.order_by(Bill.date.desc()).all()

    # 计算债务明细
    debt_details = calculate_debt_details(current_user.id)

    return render_template('index.html', bills=bills, debt_details=debt_details)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # 检查账户是否需要重置密码
            if user.needs_password_reset():
                log_login_attempt(username, user.id, False, '需要重置密码')
                flash('登录失败次数过多，请重置密码后再试', 'error')
                return render_template('login.html', users=User.query.all())

            # 检查账户是否激活
            if not user.is_active:
                log_login_attempt(username, user.id, False, '账户已禁用')
                flash('账户已被禁用，请联系管理员', 'error')
                return render_template('login.html', users=User.query.all())

            # 重置登录失败次数
            user.reset_login_attempts()
            user.update_last_login()
            db.session.commit()

            # remember=True时，关闭浏览器后仍保持登录
            login_user(user, remember=bool(remember))

            # 记录成功登录
            log_login_attempt(username, user.id, True)

            # 检查是否为默认密码，如果是则强制修改密码
            if user.is_default_password:
                flash('检测到您使用的是默认密码，为了账户安全，请先修改密码', 'warning')
                return redirect(url_for('change_password'))

            flash(f'欢迎回来，{user.display_name}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            # 登录失败处理
            if user:
                user.increment_login_attempts()
                db.session.commit()

                # 记录登录失败
                log_login_attempt(username, user.id, False, '密码错误')

                if user.needs_password_reset():
                    flash(f'登录失败次数过多，请重置密码', 'error')
                else:
                    max_attempts = SystemConfig.get_config('security.max_login_attempts', 5)
                    remaining_attempts = max_attempts - user.login_attempts
                    flash(f'用户名或密码错误，还有{remaining_attempts}次尝试机会', 'error')
            else:
                # 用户不存在，记录失败日志
                log_login_attempt(username, None, False, '用户不存在')
                flash('用户名或密码错误', 'error')

    # 获取所有用户用于登录选择
    users = User.query.all()
    return render_template('login.html', users=users)

@app.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    """重置用户密码为默认密码"""
    user = User.query.get_or_404(user_id)

    # 检查用户是否确实需要重置密码
    if not user.needs_password_reset():
        flash('该用户不需要重置密码', 'error')
        return redirect(url_for('login'))

    # 重置密码
    user.reset_to_default_password()
    db.session.commit()

    # 记录重置密码的操作
    log_login_attempt(user.username, user.id, True, '密码已重置')

    flash(f'用户 {user.display_name} 的密码已重置为默认密码 password123，请重新登录', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'error')
            return render_template('change_password.html')

        # 验证新密码确认
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('change_password.html')

        # 验证新密码强度
        password_errors = validate_password_strength(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('change_password.html')

        # 检查新密码是否与当前密码相同
        if current_user.check_password(new_password):
            flash('新密码不能与当前密码相同', 'error')
            return render_template('change_password.html')

        # 更新密码
        current_user.set_password(new_password)
        current_user.is_default_password = False  # 标记不再是默认密码
        current_user.reset_login_attempts()  # 重置登录失败次数
        db.session.commit()

        flash('密码修改成功！', 'success')
        return redirect(url_for('index'))

    return render_template('change_password.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """个人设置页面"""
    if request.method == 'POST':
        new_display_name = request.form.get('display_name', '').strip()

        if not new_display_name:
            flash('显示名称不能为空', 'error')
            return render_template('settings.html', user=current_user)

        # 更新显示名称
        current_user.display_name = new_display_name
        db.session.commit()

        flash('个人信息更新成功！', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', user=current_user)

@app.route('/admin')
@login_required
@admin_required
def admin():
    """管理员面板"""
    users = User.query.all()

    # 计算用户统计信息
    total_users = len(users)
    active_users = sum(1 for user in users if user.is_active)
    admin_users = sum(1 for user in users if user.is_admin)
    default_password_users = sum(1 for user in users if user.is_default_password)
    locked_users = sum(1 for user in users if user.needs_password_reset())

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'admin_users': admin_users,
        'default_password_users': default_password_users,
        'locked_users': locked_users
    }

    # 获取系统配置
    configs = SystemConfig.query.order_by(SystemConfig.key).all()
    config_groups = {
        'security': [],
        'bills': [],
        'system': []
    }

    for config in configs:
        category = config.key.split('.')[0]
        if category in config_groups:
            config_groups[category].append(config)
        else:
            config_groups.setdefault('other', []).append(config)

    # 获取登录日志统计
    total_logs = LoginLog.query.count()
    success_logs = LoginLog.query.filter_by(success=True).count()
    failed_logs = total_logs - success_logs

    log_stats = {
        'total': total_logs,
        'success': success_logs,
        'failed': failed_logs,
        'success_rate': round((success_logs / total_logs * 100) if total_logs > 0 else 0, 1)
    }

    return render_template('admin.html',
                         users=users,
                         stats=stats,
                         config_groups=config_groups,
                         log_stats=log_stats)



@app.route('/admin/config', methods=['POST'])
@login_required
@admin_required
def admin_config():
    """系统配置管理（仅处理POST请求）"""
    # 更新配置值
    for key in request.form:
        if key.startswith('config_'):
            config_key = key[7:]  # 移除 'config_' 前缀
            value = request.form[key]

            # 查找并更新配置
            config = SystemConfig.query.filter_by(key=config_key).first()
            if config:
                config.value = value
                config.updated_at = datetime.utcnow()

    db.session.commit()
    flash('系统配置已更新', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    """查看登录日志"""
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # 获取筛选参数
    username_filter = request.args.get('username', '')
    success_filter = request.args.get('success', '')

    # 构建查询
    query = LoginLog.query

    if username_filter:
        query = query.filter(LoginLog.username.like(f'%{username_filter}%'))

    if success_filter:
        success_bool = success_filter.lower() == 'true'
        query = query.filter(LoginLog.success == success_bool)

    # 按时间倒序排列并分页
    logs = query.order_by(LoginLog.login_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 统计信息
    total_logs = LoginLog.query.count()
    success_logs = LoginLog.query.filter_by(success=True).count()
    failed_logs = total_logs - success_logs

    stats = {
        'total': total_logs,
        'success': success_logs,
        'failed': failed_logs,
        'success_rate': round((success_logs / total_logs * 100) if total_logs > 0 else 0, 1)
    }

    return render_template('admin_logs.html', logs=logs, stats=stats,
                         username_filter=username_filter, success_filter=success_filter)

@app.route('/add_bill', methods=['GET', 'POST'])
@login_required
def add_bill():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        bill_type = request.form.get('bill_type', 'other')
        participants = request.form.getlist('participants')

        # 获取用户选择的日期
        bill_date_str = request.form.get('bill_date')
        if bill_date_str:
            bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d')
        else:
            bill_date = datetime.now()

        # 类型映射字典
        type_names = {
            'water': '💧 水费',
            'electricity': '⚡ 电费',
            'gas': '🔥 燃气费',
            'trash': '🗑️ 垃圾费',
            'internet': '🌐 网费',
            'shopping': '🛒 超市购买',
            'food': '🍔 餐饮外卖',
            'daily': '🧻 日用品',
            'other': '📝 其它费用'
        }

        # 构建描述
        if bill_type == 'other':
            custom_desc = request.form.get('custom_description', '').strip()
            description = f"📝 {custom_desc}" if custom_desc else type_names['other']
        else:
            description = type_names.get(bill_type, '📝 其它费用')

        # 添加补充说明
        notes = request.form.get('notes', '').strip()
        if notes:
            description = f"{description} - {notes}"

        # 确保付款人也在参与人中
        if str(current_user.id) not in participants:
            participants.append(str(current_user.id))

        bill = Bill(
            payer_id=current_user.id,
            amount=amount,
            description=description,
            participants=','.join(participants),
            date=bill_date  # 使用用户选择的日期
        )

        # 处理多文件上传 - 使用优化的事务系统
        files = request.files.getlist('receipts')
        valid_files = [f for f in files if f and f.filename != '' and allowed_file(f.filename)]

        # 检查磁盘空间
        if valid_files:
            estimated_size_mb = estimate_files_size(valid_files)
            sufficient, available_mb, min_space_mb = check_sufficient_disk_space(estimated_size_mb)

            if not sufficient:
                flash(f'磁盘空间不足！需要 {estimated_size_mb:.1f}MB，但只有 {available_mb:.1f}MB 可用空间（需保留 {min_space_mb}MB）', 'error')
                return render_template('add_bill.html', users=User.query.all(), today=datetime.now().strftime('%Y-%m-%d'))

        # 先添加账单到数据库
        db.session.add(bill)
        db.session.flush()  # 获取bill.id但不提交

        try:
            # 使用事务管理器处理文件上传
            with FileUploadTransaction(bill.id) as transaction:
                for file in valid_files:
                    # 生成安全文件名
                    filename = secure_filename_with_timestamp(file.filename)

                    # 保存到临时目录
                    temp_path = transaction.save_file(file, filename)

                    # 创建Receipt记录
                    receipt = Receipt(
                        bill_id=bill.id,
                        filename=filename,
                        file_type='pdf' if filename.lower().endswith('.pdf') else 'image',
                        file_size=os.path.getsize(temp_path)
                    )
                    transaction.add_database_object(receipt)

                    # 保留对旧字段的兼容（使用第一个文件）
                    if not bill.receipt_filename:
                        bill.receipt_filename = filename
                        bill.receipt_type = receipt.file_type

                # 如果到这里没有异常，提交数据库事务
                db.session.commit()

        except Exception as e:
            # 回滚数据库事务
            db.session.rollback()
            app.logger.error(f"文件上传失败: {str(e)}")
            flash(f'文件上传失败: {str(e)}', 'error')
            return render_template('add_bill.html', users=User.query.all(), today=datetime.now().strftime('%Y-%m-%d'))

        flash(f'成功添加账单：{description} - ¥{amount}')
        return redirect(url_for('index'))

    # GET请求时，传递今天的日期作为默认值
    users = User.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_bill.html', users=users, today=today)

@app.route('/settle_individual/<int:bill_id>/<int:user_id>')
@login_required
def settle_individual(bill_id, user_id):
    """单人结算功能"""
    bill = Bill.query.get_or_404(bill_id)
    user = User.query.get_or_404(user_id)

    # 权限检查：只有账单创建者才能管理结算状态
    if current_user.id != bill.payer_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '只有账单创建者才能管理结算状态'}), 403
        flash('只有账单创建者才能管理结算状态')
        return redirect(url_for('index'))

    # 检查用户是否是该账单的参与者
    participants = bill.get_participants_list()
    if user_id not in participants:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'{user.display_name}不是该账单的参与者'}), 400
        flash(f'{user.display_name}不是该账单的参与者')
        return redirect(url_for('index'))

    # 检查是否已经结算过
    existing_settlement = Settlement.query.filter_by(bill_id=bill_id, settler_id=user_id).first()

    if existing_settlement:
        # 如果已结算，则撤销结算
        db.session.delete(existing_settlement)
        action = "撤销结算"
        is_settled = False
        settled_date = None
    else:
        # 如果未结算，则添加结算记录
        split_amount = bill.get_split_amount()
        settlement = Settlement(
            bill_id=bill_id,
            settler_id=user_id,
            settled_amount=split_amount
        )
        db.session.add(settlement)
        db.session.commit()  # Commit to get the settled_date
        action = "标记已结算"
        is_settled = True
        settled_date = settlement.settled_date

    db.session.commit()

    # 检查是否所有人都已结算，更新账单状态
    bill.is_settled = bill.check_fully_settled()
    db.session.commit()

    # 如果是AJAX请求，返回JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'{user.display_name}在账单"{bill.description}"中{action}',
            'user_settled': is_settled,
            'bill_fully_settled': bill.is_settled,
            'settled_date': settled_date.strftime('%m-%d %H:%M') if settled_date else None
        })

    flash(f'{user.display_name}在账单"{bill.description}"中{action}')
    return redirect(url_for('index'))

@app.route('/toggle_settlement/<int:bill_id>')
@login_required
def toggle_settlement(bill_id):
    """整体结算切换（保持向后兼容）"""
    bill = Bill.query.get_or_404(bill_id)

    # 权限检查：只有账单创建者才能管理结算状态
    if current_user.id != bill.payer_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '只有账单创建者才能管理结算状态'}), 403
        flash('只有账单创建者才能管理结算状态')
        return redirect(url_for('index'))

    if bill.is_settled:
        # 如果当前是已结算，则清除所有结算记录
        Settlement.query.filter_by(bill_id=bill_id).delete()
        bill.is_settled = False
        action = "未结算"
        new_status = False
    else:
        # 如果当前是未结算，则为所有参与者添加结算记录
        participants = bill.get_participants_list()
        split_amount = bill.get_split_amount()

        for user_id in participants:
            if user_id != bill.payer_id:  # 付款人不需要添加结算记录
                existing_settlement = Settlement.query.filter_by(bill_id=bill_id, settler_id=user_id).first()
                if not existing_settlement:
                    settlement = Settlement(
                        bill_id=bill_id,
                        settler_id=user_id,
                        settled_amount=split_amount
                    )
                    db.session.add(settlement)

        bill.is_settled = True
        action = "已结算"
        new_status = True

    db.session.commit()

    # 如果是AJAX请求，返回JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 获取所有参与者的结算状态
        participants = bill.get_participants_list()
        settlement_status = {}
        for user_id in participants:
            if user_id != bill.payer_id:
                settlement = Settlement.query.filter_by(bill_id=bill_id, settler_id=user_id).first()
                settlement_status[user_id] = {
                    'is_settled': settlement is not None,
                    'settled_date': settlement.settled_date.strftime('%m-%d %H:%M') if settlement else None
                }

        return jsonify({
            'success': True,
            'message': f'账单"{bill.description}"已标记为{action}',
            'is_settled': new_status,
            'settlement_status': settlement_status
        })

    flash(f'账单"{bill.description}"已标记为{action}')
    return redirect(url_for('index'))

def calculate_user_balance(user_id):
    """计算用户的应付/应收余额"""
    balance = 0.0

    # 计算用户付出的钱
    paid_bills = Bill.query.filter_by(payer_id=user_id, is_settled=False).all()
    for bill in paid_bills:
        participants = bill.get_participants_list()
        if user_id in participants:
            # 用户付了钱，应该收回其他人的份额
            split_amount = bill.get_split_amount()
            balance += bill.amount - split_amount  # 应收 = 总金额 - 自己的份额

    # 计算用户参与但没付钱的账单
    all_bills = Bill.query.filter_by(is_settled=False).all()
    for bill in all_bills:
        if bill.payer_id != user_id:  # 不是自己付的钱
            participants = bill.get_participants_list()
            if user_id in participants:
                # 用户参与了但没付钱，需要付给付款人
                split_amount = bill.get_split_amount()
                balance -= split_amount  # 应付

    return round(balance, 2)

def calculate_debt_details(user_id):
    """计算用户的具体债务关系明细（考虑单人结算）"""
    from collections import defaultdict

    i_owe = defaultdict(lambda: {'amount': 0, 'bills': []})  # 我欠别人的
    owe_me = defaultdict(lambda: {'amount': 0, 'bills': []})  # 别人欠我的

    # 获取所有账单（包括部分结算的）
    all_bills = Bill.query.all()

    for bill in all_bills:
        participants = bill.get_participants_list()
        if user_id not in participants:
            continue

        # 获取该账单的结算状态
        settlement_status = bill.get_settlement_status()
        split_amount = bill.get_split_amount()
        payer = User.query.get(bill.payer_id)

        if bill.payer_id == user_id:
            # 我是付款人，检查其他参与者是否已结算
            for participant_id in participants:
                if participant_id != user_id:
                    participant_status = settlement_status.get(participant_id)
                    if participant_status and not participant_status['is_settled']:
                        # 该参与者还未结算，欠我钱
                        participant = User.query.get(participant_id)
                        owe_me[participant.display_name]['amount'] += split_amount
                        owe_me[participant.display_name]['bills'].append(bill.description)
        else:
            # 别人是付款人，检查我是否已结算
            my_status = settlement_status.get(user_id)
            if my_status and not my_status['is_settled']:
                # 我还未结算，欠付款人钱
                i_owe[payer.display_name]['amount'] += split_amount
                i_owe[payer.display_name]['bills'].append(bill.description)

    # 转换为列表格式，四舍五入金额
    i_owe_list = []
    for user, data in i_owe.items():
        i_owe_list.append({
            'user': user,
            'amount': round(data['amount'], 2),
            'bills': data['bills']
        })

    owe_me_list = []
    for user, data in owe_me.items():
        owe_me_list.append({
            'user': user,
            'amount': round(data['amount'], 2),
            'bills': data['bills']
        })

    # 计算总计
    total_owe_me = sum(item['amount'] for item in owe_me_list)
    total_i_owe = sum(item['amount'] for item in i_owe_list)

    return {
        'i_owe': i_owe_list,
        'owe_me': owe_me_list,
        'total_i_owe': round(total_i_owe, 2),
        'total_owe_me': round(total_owe_me, 2)
    }

@app.route('/api/debt_details')
@login_required
def api_debt_details():
    """API端点：返回当前用户的债务关系数据"""
    debt_details = calculate_debt_details(current_user.id)
    return jsonify(debt_details)

@app.route('/api/receipt/<int:bill_id>')
@login_required
def api_receipt(bill_id):
    """API端点：返回账单凭证信息"""
    bill = Bill.query.get_or_404(bill_id)

    # 权限检查：只有参与者可以查看
    participants = bill.get_participants_list()
    if current_user.id not in participants:
        return jsonify({'error': '抱歉，您无权查看此凭证。只有参与该账单分摊的室友才能查看相关凭证文件。'}), 403

    # 获取所有凭证文件
    receipts = bill.receipts

    # 检查是否有凭证（兼容旧版本和新版本）
    if not receipts and not bill.receipt_filename:
        return jsonify({'error': '该账单没有凭证'}), 404

    # 构建凭证文件列表
    receipt_files = []

    # 首先添加新的Receipt记录
    for receipt in receipts:
        filepath = f"uploads/receipts/{bill.id}/{receipt.filename}"
        receipt_files.append({
            'filename': receipt.filename,
            'filepath': filepath,
            'file_type': receipt.file_type,
            'file_size': receipt.file_size,
            'upload_date': receipt.upload_date.strftime('%Y-%m-%d %H:%M')
        })

    # 如果没有新记录但有旧字段，添加旧字段（向后兼容）
    if not receipt_files and bill.receipt_filename:
        filepath = f"uploads/receipts/{bill.id}/{bill.receipt_filename}"
        receipt_files.append({
            'filename': bill.receipt_filename,
            'filepath': filepath,
            'file_type': bill.receipt_type,
            'file_size': None,
            'upload_date': None
        })

    return jsonify({
        'success': True,
        'bill_id': bill.id,
        'description': bill.description,
        'amount': float(bill.amount),
        'date': bill.date.strftime('%Y年%m月%d日'),
        'receipts': receipt_files,
        # 保留向后兼容
        'receipt_type': bill.receipt_type if bill.receipt_filename else None,
        'filepath': f"uploads/receipts/{bill.id}/{bill.receipt_filename}" if bill.receipt_filename else None,
        'filename': bill.receipt_filename
    })

@app.route('/view_receipt/<int:bill_id>')
@login_required
def view_receipt(bill_id):
    """查看账单凭证"""
    bill = Bill.query.get_or_404(bill_id)

    # 权限检查：只有参与者可以查看
    participants = bill.get_participants_list()
    if current_user.id not in participants:
        flash('抱歉，您无权查看此凭证。只有参与该账单分摊的室友才能查看相关凭证文件。')
        return redirect(url_for('index'))

    if not bill.receipt_filename:
        flash('该账单没有凭证')
        return redirect(url_for('index'))

    # 构建文件路径
    filepath = f"uploads/receipts/{bill.id}/{bill.receipt_filename}"

    return render_template('view_receipt.html',
                         bill=bill,
                         filepath=filepath)

@app.route('/dashboard')
@login_required
def dashboard():
    """个人统计面板"""
    user_id = current_user.id

    # 统计数据
    bills_count = Bill.query.filter_by(payer_id=user_id).count()

    # 计算参与的账单数（包含用户ID的账单）
    participated_bills_count = Bill.query.filter(Bill.participants.contains(str(user_id))).count()

    # 计算已结清的账单数（对用户而言没有未结债务的账单）
    debt_details = calculate_debt_details(user_id)
    settled_bills_count = 0

    # 遍历所有用户参与的账单，统计已结清的
    all_participated_bills = Bill.query.filter(Bill.participants.contains(str(user_id))).all()
    for bill in all_participated_bills:
        settlement_status = bill.get_settlement_status()
        user_status = settlement_status.get(user_id)
        if user_status and user_status['is_settled']:
            settled_bills_count += 1

    # 待收款总额和待付款总额
    total_owe_me = debt_details['total_owe_me']
    total_i_owe = debt_details['total_i_owe']

    # 最近的账单
    recent_bills = Bill.query.filter_by(payer_id=user_id).order_by(Bill.date.desc()).limit(5).all()

    return render_template('dashboard.html',
                         total_owe_me=total_owe_me,
                         total_i_owe=total_i_owe,
                         bills_count=bills_count,
                         participated_bills_count=participated_bills_count,
                         settled_bills_count=settled_bills_count,
                         debt_details=debt_details,
                         recent_bills=recent_bills)

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """
    服务上传的文件
    使用 send_from_directory 安全地提供文件访问
    """
    try:
        # 使用static/uploads作为基础路径，filename已经包含receipts/部分
        uploads_base = os.path.join(app.root_path, 'static', 'uploads')
        full_path = os.path.join(uploads_base, filename)
        print(f"请求文件: {filename}")
        print(f"搜索基础路径: {uploads_base}")
        print(f"完整路径: {full_path}")
        print(f"文件存在: {os.path.exists(full_path)}")

        return send_from_directory(uploads_base, filename)
    except FileNotFoundError as e:
        print(f"文件未找到错误: {e}")
        return f"文件未找到: {filename}", 404

@app.route('/delete_bill/<int:bill_id>', methods=['POST'])
@login_required
def delete_bill(bill_id):
    """
    删除账单
    只有账单创建者可以删除账单
    """
    bill = Bill.query.get_or_404(bill_id)

    # 权限检查：只有账单创建者可以删除
    if bill.payer_id != current_user.id:
        return jsonify({'error': '只有账单创建者可以删除账单'}), 403

    try:
        # 获取需要删除的文件信息（用于确认消息）
        receipts_count = len(bill.receipts)
        settlements_count = len(bill.settlements)

        # 先收集要删除的文件路径列表
        files_to_delete = []
        for receipt in bill.receipts:
            # 使用账单ID创建正确的文件路径（文件存储在子目录中）
            file_path = os.path.join(UPLOAD_FOLDER, str(bill_id), receipt.filename)
            if os.path.exists(file_path):
                files_to_delete.append(file_path)

        # 先删除数据库记录（级联删除会自动删除settlements和receipts记录）
        db.session.delete(bill)
        db.session.commit()
        print(f"数据库删除成功：账单{bill_id}及其关联记录")

        # 数据库删除成功后再删除文件
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"已删除凭证文件: {file_path}")
            except OSError as e:
                print(f"删除文件失败: {file_path}, 错误: {e}")

        # 删除账单文件夹（如果为空）
        bill_folder = os.path.join(UPLOAD_FOLDER, str(bill_id))
        try:
            if os.path.exists(bill_folder) and not os.listdir(bill_folder):
                os.rmdir(bill_folder)
                print(f"已删除空目录: {bill_folder}")
        except OSError as e:
            print(f"删除目录失败: {bill_folder}, 错误: {e}")

        flash(f'账单已删除！同时删除了 {settlements_count} 个结算记录和 {receipts_count} 个凭证文件。', 'success')
        return jsonify({'success': True, 'message': '账单删除成功'})

    except Exception as e:
        db.session.rollback()
        print(f"删除账单时发生错误: {e}")
        return jsonify({'error': '删除失败，请稍后重试'}), 500

@app.route('/edit_bill/<int:bill_id>', methods=['GET', 'POST'])
@login_required
def edit_bill(bill_id):
    """
    编辑账单
    只有账单创建者可以编辑账单
    """
    bill = Bill.query.get_or_404(bill_id)

    # 权限检查：只有账单创建者可以编辑
    if bill.payer_id != current_user.id:
        flash('只有账单创建者可以编辑账单', 'error')
        return redirect(url_for('index'))

    users = User.query.all()

    if request.method == 'POST':
        try:
            old_amount = bill.amount
            old_participants = bill.participants

            # 更新账单信息
            bill.description = request.form['description']
            bill.amount = float(request.form['amount'])
            bill.date = datetime.strptime(request.form['date'], '%Y-%m-%d')

            # 处理参与者（确保付款人始终被包含）
            selected_participants = request.form.getlist('participants')
            payer_id_str = str(bill.payer_id)
            if payer_id_str not in selected_participants:
                selected_participants.append(payer_id_str)
            bill.participants = ','.join(selected_participants)

            # 检查是否修改了影响结算的字段（金额或参与者）
            amount_changed = bill.amount != old_amount
            participants_changed = bill.participants != old_participants

            if amount_changed or participants_changed:
                # 删除所有现有的结算记录
                Settlement.query.filter_by(bill_id=bill.id).delete()
                bill.is_settled = False
                flash('由于修改了金额或参与者，已清除原有结算记录，需要重新结算。', 'warning')

            # 处理新上传的文件
            uploaded_files = request.files.getlist('receipts')
            for file in uploaded_files:
                if file and file.filename and allowed_file(file.filename):
                    # 创建账单专属目录
                    bill_folder = os.path.join(UPLOAD_FOLDER, str(bill.id))
                    os.makedirs(bill_folder, exist_ok=True)

                    # 生成安全的文件名
                    filename = secure_filename_with_timestamp(file.filename)
                    file_path = os.path.join(bill_folder, filename)
                    file.save(file_path)

                    # 确定文件类型
                    file_type = 'pdf' if filename.lower().endswith('.pdf') else 'image'

                    # 获取文件大小
                    file_size = os.path.getsize(file_path)

                    # 保存到数据库
                    receipt = Receipt(
                        bill_id=bill.id,
                        filename=filename,
                        file_type=file_type,
                        file_size=file_size
                    )
                    db.session.add(receipt)

            db.session.commit()
            flash('账单修改成功！', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            print(f"修改账单时发生错误: {e}")
            flash('修改失败，请检查输入信息', 'error')

    return render_template('edit_bill.html', bill=bill, users=users)

@app.route('/api/delete_receipt/<int:receipt_id>', methods=['DELETE'])
@login_required
def delete_receipt(receipt_id):
    """
    删除单个凭证文件
    只有账单创建者可以删除凭证
    """
    receipt = Receipt.query.get_or_404(receipt_id)
    bill = receipt.bill

    # 权限检查：只有账单创建者可以删除凭证
    if bill.payer_id != current_user.id:
        return jsonify({'error': '只有账单创建者可以删除凭证'}), 403

    try:
        # 删除文件系统中的文件
        file_path = os.path.join(UPLOAD_FOLDER, str(bill.id), receipt.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"已删除凭证文件: {file_path}")

        # 删除数据库记录
        db.session.delete(receipt)
        db.session.commit()

        return jsonify({'success': True, 'message': '凭证删除成功'})

    except Exception as e:
        db.session.rollback()
        print(f"删除凭证时发生错误: {e}")
        return jsonify({'error': '删除失败，请稍后重试'}), 500

# ===========================
# 健康检查和监控端点
# ===========================

@app.route('/health')
def health_check():
    """系统健康检查端点"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.4',
            'checks': {}
        }

        # 检查数据库连接
        try:
            User.query.count()
            health_status['checks']['database'] = {'status': 'ok', 'message': '数据库连接正常'}
        except Exception as e:
            health_status['checks']['database'] = {'status': 'error', 'message': f'数据库连接失败: {str(e)}'}
            health_status['status'] = 'unhealthy'

        # 检查磁盘空间
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            free_mb = free // (1024*1024)
            total_mb = total // (1024*1024)
            used_percent = round((used / total) * 100, 1)

            health_status['checks']['disk_space'] = {
                'status': 'ok' if free_mb > 100 else 'warning',
                'free_mb': free_mb,
                'total_mb': total_mb,
                'used_percent': used_percent
            }

            if free_mb <= 50:
                health_status['status'] = 'unhealthy'
            elif free_mb <= 100:
                health_status['status'] = 'degraded'

        except Exception as e:
            health_status['checks']['disk_space'] = {'status': 'error', 'message': f'磁盘检查失败: {str(e)}'}

        # 检查上传目录权限
        try:
            test_file = os.path.join(UPLOAD_FOLDER, '.health_check')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            health_status['checks']['upload_directory'] = {'status': 'ok', 'message': '上传目录可写'}
        except Exception as e:
            health_status['checks']['upload_directory'] = {'status': 'error', 'message': f'上传目录不可写: {str(e)}'}
            health_status['status'] = 'unhealthy'

        # 检查活跃用户数
        try:
            active_users = User.query.filter_by(is_active=True).count()
            total_bills = Bill.query.count()

            health_status['checks']['application'] = {
                'status': 'ok',
                'active_users': active_users,
                'total_bills': total_bills
            }
        except Exception as e:
            health_status['checks']['application'] = {'status': 'error', 'message': f'应用状态检查失败: {str(e)}'}

        # 设置HTTP状态码
        status_code = 200
        if health_status['status'] == 'unhealthy':
            status_code = 503
        elif health_status['status'] == 'degraded':
            status_code = 200  # 降级但仍可用

        return jsonify(health_status), status_code

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'健康检查失败: {str(e)}'
        }), 503

@app.route('/metrics')
def metrics():
    """系统指标端点（简化版Prometheus格式）"""
    try:
        # 基础指标
        user_count = User.query.count()
        bill_count = Bill.query.count()
        settlement_count = Settlement.query.count()
        receipt_count = Receipt.query.count()

        # 磁盘使用情况
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            disk_usage_bytes = used
            disk_total_bytes = total
        except:
            disk_usage_bytes = 0
            disk_total_bytes = 0

        # 上传文件总大小
        total_upload_size = 0
        try:
            for receipt in Receipt.query.all():
                if receipt.file_size:
                    total_upload_size += receipt.file_size
        except:
            pass

        metrics_data = f"""# HELP roommate_bills_users_total Total number of users
# TYPE roommate_bills_users_total counter
roommate_bills_users_total {user_count}

# HELP roommate_bills_bills_total Total number of bills
# TYPE roommate_bills_bills_total counter
roommate_bills_bills_total {bill_count}

# HELP roommate_bills_settlements_total Total number of settlements
# TYPE roommate_bills_settlements_total counter
roommate_bills_settlements_total {settlement_count}

# HELP roommate_bills_receipts_total Total number of receipts
# TYPE roommate_bills_receipts_total counter
roommate_bills_receipts_total {receipt_count}

# HELP roommate_bills_upload_size_bytes Total size of uploaded files
# TYPE roommate_bills_upload_size_bytes gauge
roommate_bills_upload_size_bytes {total_upload_size}

# HELP roommate_bills_disk_usage_bytes Current disk usage
# TYPE roommate_bills_disk_usage_bytes gauge
roommate_bills_disk_usage_bytes {disk_usage_bytes}

# HELP roommate_bills_disk_total_bytes Total disk space
# TYPE roommate_bills_disk_total_bytes gauge
roommate_bills_disk_total_bytes {disk_total_bytes}
"""

        return metrics_data, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        return f"# Error generating metrics: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=7769)