"""
室友记账系统配置文件
支持开发环境和生产环境的不同配置
"""
import os
import secrets
from datetime import timedelta

class Config:
    """基础配置类"""
    # 强制使用项目目录内的绝对路径
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # 数据库配置
    INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
    DB_PATH = os.path.join(INSTANCE_PATH, 'database.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'receipts')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # 会话配置
    SESSION_COOKIE_NAME = 'roommate_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # 在HTTPS环境中应设为True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Flask-Login配置
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    SESSION_PROTECTION = 'strong'

    # 服务器配置
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 7769))

    # 磁盘空间阈值（MB）
    MIN_DISK_SPACE_MB = int(os.environ.get('MIN_DISK_SPACE_MB', 100))

    @staticmethod
    def init_app(app):
        """初始化Flask应用配置"""
        # 确保必要目录存在
        os.makedirs(Config.INSTANCE_PATH, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        print(f"数据库路径: {Config.DB_PATH}")
        print(f"上传路径: {Config.UPLOAD_FOLDER}")

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

    # 开发环境可以启用更详细的日志
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

    # 生产环境的安全配置
    SESSION_COOKIE_SECURE = os.environ.get('HTTPS', 'false').lower() == 'true'

    # 生产环境日志级别
    LOG_LEVEL = 'INFO'

    # 生产环境性能配置
    THREADED = True

    @staticmethod
    def init_app(app):
        """生产环境特定初始化"""
        Config.init_app(app)

        # 生产环境检查
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True

    # 测试环境使用内存数据库
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # 禁用CSRF保护以便测试
    WTF_CSRF_ENABLED = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """根据环境变量获取配置类"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])