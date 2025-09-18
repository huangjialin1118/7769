#!/usr/bin/env python3
"""
室友记账系统启动脚本
支持开发和生产环境的启动配置
"""
import os
import sys
import logging
from config import get_config

def check_python_version():
    """检查Python版本兼容性"""
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)

    print(f"✅ Python版本: {sys.version.split()[0]}")

def check_disk_space():
    """检查磁盘空间"""
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_mb = free // (1024*1024)

        config_class = get_config()
        min_space = getattr(config_class, 'MIN_DISK_SPACE_MB', 100)

        if free_mb < min_space:
            print(f"⚠️  警告: 磁盘空间不足 ({free_mb}MB < {min_space}MB)")
            return False

        print(f"✅ 磁盘空间: {free_mb}MB 可用")
        return True
    except Exception as e:
        print(f"⚠️  无法检查磁盘空间: {e}")
        return True

def setup_logging():
    """设置日志配置"""
    config_class = get_config()
    log_level = getattr(config_class, 'LOG_LEVEL', 'INFO')

    # 创建logs目录
    os.makedirs('logs', exist_ok=True)

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """主启动函数"""
    print("🏠 室友记账系统启动中...")

    # 检查环境
    check_python_version()

    # 检查磁盘空间
    if not check_disk_space():
        response = input("磁盘空间不足，是否继续启动？(y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    # 设置日志
    setup_logging()

    # 获取配置
    config_class = get_config()
    env_name = os.environ.get('FLASK_ENV', 'development')

    print(f"🔧 环境配置: {env_name}")
    print(f"🐛 调试模式: {config_class.DEBUG}")

    # 导入Flask应用
    try:
        from app import app, init_database

        # 应用配置
        app.config.from_object(config_class)
        config_class.init_app(app)

        # 初始化数据库
        with app.app_context():
            init_database()

        print(f"🌐 服务器启动: http://{config_class.HOST}:{config_class.PORT}")
        print("📝 默认账户: roommate1-4/password123")

        if config_class.DEBUG:
            print("⚠️  开发模式运行 - 请勿用于生产环境")
        else:
            print("🔒 生产模式运行")

        # 启动服务器
        app.run(
            debug=config_class.DEBUG,
            host=config_class.HOST,
            port=config_class.PORT,
            threaded=getattr(config_class, 'THREADED', True)
        )

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖已安装: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logging.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()