from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 新增安全相关字段
    is_default_password = db.Column(db.Boolean, default=True, nullable=False)  # 是否使用默认密码
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # 是否为管理员
    last_login = db.Column(db.DateTime)  # 最后登录时间
    login_attempts = db.Column(db.Integer, default=0, nullable=False)  # 登录失败次数
    locked_until = db.Column(db.DateTime)  # 账户锁定到期时间
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # 账户是否激活

    # 关系
    bills_paid = db.relationship('Bill', backref='payer', lazy=True, foreign_keys='Bill.payer_id')
    settlements = db.relationship('Settlement', backref='settler', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def needs_password_reset(self):
        """检查是否需要重置密码（登录失败次数过多）"""
        max_attempts = SystemConfig.get_config('security.max_login_attempts', 5)
        return self.login_attempts >= max_attempts

    def lock_account(self, duration_minutes=15):
        """锁定账户指定时间（分钟）"""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)

    def reset_to_default_password(self):
        """重置为默认密码并清除失败记录"""
        self.set_password('password123')  # 重置为默认密码
        self.login_attempts = 0  # 清除失败次数
        self.is_default_password = True  # 标记为使用默认密码
        self.locked_until = None  # 清除锁定时间（如果有的话）

    def increment_login_attempts(self):
        """增加登录失败次数"""
        self.login_attempts += 1
        # 不再锁定账户，而是在达到上限时等待用户主动重置密码

    def reset_login_attempts(self):
        """重置登录失败次数"""
        self.login_attempts = 0

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()

    def __repr__(self):
        return f'<User {self.username}>'

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    participants = db.Column(db.String(50), nullable=False)  # 存储参与人ID，逗号分隔
    is_settled = db.Column(db.Boolean, default=False)
    receipt_filename = db.Column(db.String(200))  # 凭证文件名
    receipt_type = db.Column(db.String(10))  # 文件类型（pdf/image）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    settlements = db.relationship('Settlement', backref='bill', lazy=True)
    receipts = db.relationship('Receipt', backref='bill', lazy=True, cascade='all, delete-orphan')

    def get_participants_list(self):
        """返回参与人ID列表"""
        if self.participants:
            return [int(x) for x in self.participants.split(',') if x.strip()]
        return []

    def get_split_amount(self):
        """计算每人应付金额"""
        participants_count = len(self.get_participants_list())
        if participants_count > 0:
            return round(self.amount / participants_count, 2)
        return 0

    def get_settlement_status(self):
        """获取每个参与者的结算状态"""

        participants = self.get_participants_list()
        split_amount = self.get_split_amount()
        settlement_status = {}

        # 获取已有的结算记录
        settled_users = {}
        for settlement in self.settlements:
            settled_users[settlement.settler_id] = {
                'amount': settlement.settled_amount,
                'date': settlement.settled_date,
                'is_settled': True
            }

        # 为每个参与者生成状态
        for user_id in participants:
            user = User.query.get(user_id)
            if user:
                is_payer = user_id == self.payer_id
                settlement_status[user_id] = {
                    'user': user,
                    'is_payer': is_payer,
                    'expected_amount': 0 if is_payer else split_amount,  # 付款人不需要再付
                    'is_settled': user_id in settled_users or is_payer,  # 付款人算已结算
                    'settled_amount': settled_users.get(user_id, {}).get('amount', 0),
                    'settled_date': settled_users.get(user_id, {}).get('date', None)
                }

        return settlement_status

    def get_settlement_progress(self):
        """获取结算进度"""
        settlement_status = self.get_settlement_status()
        if not settlement_status:
            return {'settled': 0, 'total': 0, 'percentage': 0}

        settled_count = sum(1 for status in settlement_status.values() if status['is_settled'])
        total_count = len(settlement_status)
        percentage = round((settled_count / total_count) * 100) if total_count > 0 else 0

        return {
            'settled': settled_count,
            'total': total_count,
            'percentage': percentage
        }

    def check_fully_settled(self):
        """检查是否全部结算"""
        progress = self.get_settlement_progress()
        return progress['settled'] == progress['total'] and progress['total'] > 0

    def get_unsettled_participants(self):
        """获取未结算的参与者列表"""
        settlement_status = self.get_settlement_status()
        return [
            status for status in settlement_status.values()
            if not status['is_settled'] and not status['is_payer']
        ]

    def __repr__(self):
        return f'<Bill {self.description}: {self.amount}>'

class Settlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    settler_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    settled_amount = db.Column(db.Float, nullable=False)
    settled_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Settlement {self.settler_id} paid {self.settled_amount} for bill {self.bill_id}>'

class Receipt(db.Model):
    """账单凭证模型（支持多文件）"""
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf/image
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Receipt {self.filename} for bill {self.bill_id}>'

class SystemConfig(db.Model):
    """系统配置模型（键值对存储）"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(200))  # 配置项描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_config(key, default_value=None):
        """获取配置值"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            # 尝试转换为合适的类型
            try:
                # 处理布尔值
                if config.value.lower() in ['true', 'false']:
                    return config.value.lower() == 'true'
                # 处理整数
                if config.value.isdigit():
                    return int(config.value)
                # 处理浮点数
                if '.' in config.value and config.value.replace('.', '').isdigit():
                    return float(config.value)
                # 返回字符串
                return config.value
            except:
                return config.value
        return default_value

    @staticmethod
    def set_config(key, value, description=None):
        """设置配置值"""
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = str(value)
            config.updated_at = datetime.utcnow()
            if description:
                config.description = description
        else:
            config = SystemConfig(
                key=key,
                value=str(value),
                description=description
            )
            db.session.add(config)

    def __repr__(self):
        return f'<SystemConfig {self.key}={self.value}>'

class LoginLog(db.Model):
    """登录日志模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(80), nullable=False)  # 记录用户名，即使用户被删除也能查看
    ip_address = db.Column(db.String(45))  # IPv4和IPv6地址
    user_agent = db.Column(db.String(500))  # 浏览器信息
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, nullable=False)  # 登录是否成功
    failure_reason = db.Column(db.String(200))  # 失败原因

    # 关系
    user = db.relationship('User', backref='login_logs', lazy=True)

    def __repr__(self):
        status = "成功" if self.success else "失败"
        return f'<LoginLog {self.username} {status} at {self.login_time}>'