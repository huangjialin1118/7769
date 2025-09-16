# 室友记账系统 (Roommate Bills) - Claude 配置

这是一个用于室友之间分摊账单的 Flask Web 应用程序。

## 项目结构

```
roommate-bills/
├── app.py                 # Flask 主应用文件
├── models.py              # 数据库模型定义
├── run.sh                 # 启动脚本（可选）
├── templates/             # HTML 模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── login.html        # 登录页
│   ├── add_bill.html     # 添加账单页
│   └── dashboard.html    # 个人面板
├── static/               # 静态资源
│   ├── css/style.css    # 样式文件
│   ├── js/main.js       # JavaScript文件
│   └── uploads/         # 上传文件存储
│       └── receipts/    # 凭证文件存储目录
├── instance/            # Flask实例文件夹
│   └── database.db      # SQLite数据库
└── venv/               # Python虚拟环境
```

## 技术栈

- **后端**: Python Flask + SQLAlchemy ORM
- **前端**: Bootstrap 5 + JavaScript
- **数据库**: SQLite
- **文件上传**: Werkzeug
- **身份认证**: Flask-Login

## 主要功能

1. **用户管理**: 登录/登出功能
2. **账单管理**:
   - 添加账单（支持多种类型和日期选择）
   - 多文件凭证上传（拖拽支持）
   - 实时分摊计算
3. **结算管理**:
   - 单人结算/撤销
   - 全部结算/撤销
   - 实时UI更新（无刷新）
4. **凭证查看**: 模态框查看多文件凭证
5. **数据统计**: 债务详情和快速统计

## 开发环境

- Python 3.12+
- Flask开发服务器运行在端口7769
- 使用虚拟环境管理依赖（可选）

## 启动方式

### 方式1：直接启动（推荐）
```bash
# 使用绝对路径配置，无需考虑工作目录
python3 app.py
# 或使用虚拟环境
source venv/bin/activate && python app.py
```

### 方式2：使用启动脚本
```bash
# 自动检测环境并启动
./run.sh
```

## 路径配置

系统使用**绝对路径配置**，确保在任何目录下运行都能正常工作：

- **数据库**: `{项目根目录}/instance/database.db`
- **上传文件**: `{项目根目录}/static/uploads/receipts/`
- **支持跨平台**: 兼容 macOS、Linux、Windows 和树莓派

## 常用命令

```bash
# 启动开发服务器
python3 app.py

# 停止服务器
lsof -ti :7769 | xargs kill -9

# 检查用户
python3 -c "from app import app, db; from models import User; app.app_context().push(); [print(f'{u.username}/{\"password123\"} -> {u.display_name}') for u in User.query.all()]"

# 重置数据库
rm instance/database.db && python3 app.py
```

## 默认用户

- roommate1/password123 → 室友1
- roommate2/password123 → 室友2
- roommate3/password123 → 室友3
- roommate4/password123 → 室友4

## 数据库模型

- **User**: 用户表
- **Bill**: 账单表
- **Settlement**: 结算记录表
- **Receipt**: 凭证文件表（支持多文件）

## 部署说明

### 树莓派部署
1. 传输项目文件到树莓派
2. 安装依赖：`pip3 install flask flask-sqlalchemy flask-login werkzeug`
3. 直接运行：`python3 app.py`
4. 或创建系统服务实现开机自启

### Docker部署（未来支持）
- 支持容器化部署
- 数据持久化配置
- 环境变量配置

## 开发注意事项

- ✅ **路径问题已解决**: 使用绝对路径，无需依赖工作目录
- ✅ **文件上传正常**: 凭证文件路径修复，支持多文件上传
- ✅ **跨IDE兼容**: VS Code、PyCharm等IDE直接运行
- 数据库自动初始化，首次运行会创建默认用户
- 支持图片和PDF凭证文件
- 所有结算操作使用AJAX实现实时更新
- Bootstrap 5用于响应式UI设计

## 测试步骤

1. 直接运行 `python3 app.py`
2. 访问 http://127.0.0.1:7769
3. 使用任意默认账户登录
4. 添加账单并上传多个凭证文件
5. 测试拖拽上传功能
6. 测试结算/撤销功能
7. 查看凭证模态框多文件切换

## 故障排除

### 端口占用
```bash
lsof -ti :7769 | xargs kill -9
```

### 数据库问题
```bash
rm instance/database.db
python3 app.py  # 重新创建
```

### 文件访问404
- 已修复：使用正确的静态文件路径
- 凭证文件通过 `/uploads/` 路由访问