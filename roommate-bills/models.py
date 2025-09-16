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

    # 关系
    bills_paid = db.relationship('Bill', backref='payer', lazy=True, foreign_keys='Bill.payer_id')
    settlements = db.relationship('Settlement', backref='settler', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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