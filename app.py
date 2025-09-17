from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Bill, Settlement, Receipt
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import secrets

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

def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_with_timestamp(filename):
    """为文件名添加时间戳以避免冲突"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{timestamp}_{name}{ext}"

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

        for roommate in roommates:
            user = User(username=roommate['username'], display_name=roommate['display_name'])
            user.set_password(roommate['password'])
            db.session.add(user)

        db.session.commit()
        print("已创建默认用户账号")

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
            # remember=True时，关闭浏览器后仍保持登录
            login_user(user, remember=bool(remember))
            flash(f'欢迎回来，{user.display_name}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'error')

    # 获取所有用户用于登录选择
    users = User.query.all()
    return render_template('login.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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

        # 先添加账单到数据库
        db.session.add(bill)
        db.session.flush()  # 获取bill.id但不提交

        # 处理多文件上传
        files = request.files.getlist('receipts')
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                # 创建账单专属目录
                bill_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(bill.id))
                os.makedirs(bill_folder, exist_ok=True)

                # 保存文件
                filename = secure_filename_with_timestamp(file.filename)
                filepath = os.path.join(bill_folder, filename)
                file.save(filepath)

                # 创建Receipt记录
                receipt = Receipt(
                    bill_id=bill.id,
                    filename=filename,
                    file_type='pdf' if filename.lower().endswith('.pdf') else 'image',
                    file_size=os.path.getsize(filepath)
                )
                db.session.add(receipt)

                # 保留对旧字段的兼容（使用第一个文件）
                if not bill.receipt_filename:
                    bill.receipt_filename = filename
                    bill.receipt_type = receipt.file_type

        # 提交所有更改
        db.session.commit()

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

        # 删除关联的凭证文件（从文件系统）
        for receipt in bill.receipts:
            # 使用账单ID创建正确的文件路径（文件存储在子目录中）
            file_path = os.path.join(UPLOAD_FOLDER, str(bill_id), receipt.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"已删除凭证文件: {file_path}")

        # 删除账单文件夹（如果为空）
        bill_folder = os.path.join(UPLOAD_FOLDER, str(bill_id))
        try:
            if os.path.exists(bill_folder) and not os.listdir(bill_folder):
                os.rmdir(bill_folder)
                print(f"已删除空目录: {bill_folder}")
        except OSError:
            pass  # 目录不为空或其他问题，忽略

        # 删除账单（级联删除会自动删除settlements和receipts记录）
        db.session.delete(bill)
        db.session.commit()

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

            # 处理参与者
            selected_participants = request.form.getlist('participants')
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
                    # 确保上传目录存在
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                    # 生成安全的文件名
                    filename = secure_filename_with_timestamp(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
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
        file_path = os.path.join(UPLOAD_FOLDER, receipt.filename)
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

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=7769)