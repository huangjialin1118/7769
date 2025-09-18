#!/bin/bash

# 室友记账系统 - 树莓派一键部署脚本
# 使用方法: bash deploy_raspberry.sh

set -e  # 发生错误时停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 输出函数
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 检测系统信息
detect_system() {
    info "检测系统信息..."

    OS=$(uname -s)
    ARCH=$(uname -m)

    echo "操作系统: $OS"
    echo "架构: $ARCH"

    # 检查是否为树莓派
    if [[ -f /proc/device-tree/model ]]; then
        PI_MODEL=$(cat /proc/device-tree/model)
        info "检测到树莓派: $PI_MODEL"
    fi

    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        info "Python版本: $PYTHON_VERSION"

        # 检查版本是否满足要求 (>= 3.6)
        MIN_VERSION="3.6"
        if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,6) else 1)" 2>/dev/null; then
            error "Python版本过低，需要3.6或更高版本"
            exit 1
        fi
        success "Python版本符合要求"
    else
        error "未找到Python3，请先安装Python3"
        exit 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    info "检查磁盘空间..."

    AVAILABLE=$(df . | awk 'NR==2 {print $4}')
    AVAILABLE_MB=$((AVAILABLE / 1024))

    echo "可用空间: ${AVAILABLE_MB}MB"

    if [[ $AVAILABLE_MB -lt 500 ]]; then
        warning "磁盘空间不足500MB，建议清理后再安装"
        read -p "是否继续安装？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 安装依赖
install_dependencies() {
    info "安装Python依赖..."

    # 检查pip3
    if ! command -v pip3 &> /dev/null; then
        error "pip3未找到，请先安装pip3"
        info "运行: sudo apt update && sudo apt install python3-pip"
        exit 1
    fi

    # 升级pip
    python3 -m pip install --upgrade pip --user

    # 安装依赖
    if [[ -f requirements.txt ]]; then
        python3 -m pip install -r requirements.txt --user
        success "依赖安装完成"
    else
        warning "requirements.txt未找到，手动安装核心依赖"
        python3 -m pip install flask flask-sqlalchemy flask-login werkzeug --user
    fi
}

# 创建systemd服务
create_systemd_service() {
    info "创建systemd服务..."

    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)

    # 检查是否存在服务文件
    if [[ -f roommate-bills.service ]]; then
        warning "发现现有服务文件，准备安装..."
    else
        info "创建新的服务文件..."
        cat > roommate-bills.service << EOF
[Unit]
Description=Roommate Bills Management System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="FLASK_ENV=production"
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    fi

    # 安装服务
    sudo cp roommate-bills.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable roommate-bills

    success "systemd服务已创建并启用"
}

# 配置防火墙
configure_firewall() {
    info "配置防火墙..."

    # 检查ufw是否存在
    if command -v ufw &> /dev/null; then
        sudo ufw allow 7769/tcp
        success "防火墙规则已添加 (端口7769)"
    else
        warning "ufw未安装，请手动配置防火墙开放端口7769"
    fi
}

# 创建环境配置文件
create_env_file() {
    info "创建环境配置..."

    if [[ ! -f .env ]]; then
        cat > .env << EOF
# 室友记账系统环境配置
FLASK_ENV=production
HOST=0.0.0.0
PORT=7769
MAX_UPLOAD_SIZE=10485760
MIN_DISK_SPACE_MB=100

# 生产环境请修改这个密钥
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF
        success "环境配置文件已创建: .env"
    else
        warning ".env文件已存在，跳过创建"
    fi
}

# 初始化应用
initialize_app() {
    info "初始化应用..."

    # 创建必要目录
    mkdir -p instance
    mkdir -p static/uploads/receipts
    mkdir -p logs

    # 设置权限
    chmod 755 instance
    chmod 755 static/uploads/receipts
    chmod 755 logs

    success "应用初始化完成"
}

# 启动服务
start_service() {
    info "启动服务..."

    # 停止现有服务（如果运行中）
    sudo systemctl stop roommate-bills 2>/dev/null || true

    # 启动服务
    sudo systemctl start roommate-bills

    # 检查状态
    sleep 3
    if sudo systemctl is-active --quiet roommate-bills; then
        success "服务启动成功！"

        # 获取IP地址
        LOCAL_IP=$(hostname -I | cut -d' ' -f1)

        echo ""
        echo "🎉 部署完成！"
        echo ""
        echo "📱 访问地址:"
        echo "   本地: http://localhost:7769"
        echo "   局域网: http://$LOCAL_IP:7769"
        echo ""
        echo "👥 默认账户:"
        echo "   roommate1/password123 (管理员)"
        echo "   roommate2/password123"
        echo "   roommate3/password123"
        echo "   roommate4/password123"
        echo ""
        echo "🔧 服务管理命令:"
        echo "   启动: sudo systemctl start roommate-bills"
        echo "   停止: sudo systemctl stop roommate-bills"
        echo "   重启: sudo systemctl restart roommate-bills"
        echo "   状态: sudo systemctl status roommate-bills"
        echo "   日志: sudo journalctl -u roommate-bills -f"
        echo ""

    else
        error "服务启动失败"
        echo "查看错误日志: sudo journalctl -u roommate-bills -n 20"
        exit 1
    fi
}

# 主函数
main() {
    echo "🏠 室友记账系统 - 树莓派部署脚本"
    echo "=================================="
    echo ""

    check_root
    detect_system
    check_disk_space
    install_dependencies
    create_env_file
    initialize_app
    create_systemd_service
    configure_firewall
    start_service
}

# 运行主函数
main "$@"