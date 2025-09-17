# 室友记账系统

一个基于 Flask 的室友账单管理和分摊系统，支持多文件凭证上传和实时结算跟踪。

[English](README.md) | 中文文档

## ✨ 功能特色

### 📊 账单管理
- **智能账单分类**: 预设分类（水电费、购物、餐饮等）和自定义选项
- **日期选择**: 可选择实际账单日期，便于更好的追踪
- **实时计算**: 自动费用分摊，提供实时预览
- **多人参与**: 可选择哪些室友参与每笔账单的分摊
- **编辑账单**: 修改已存在的账单（仅创建者可编辑）
- **删除账单**: 删除账单及关联数据（仅创建者可删除）
- **权限控制**: 只有账单创建者才能编辑或删除账单

### 📎 凭证管理
- **多文件上传**: 每笔账单支持上传多个凭证（图片 + PDF）
- **拖拽上传**: 直观的拖拽界面
- **文件管理**: 提交前可预览、删除文件
- **模态查看器**: 在放大的模态框中查看凭证，多文件支持标签页切换

### 💰 结算系统
- **单人结算**: 标记特定室友已付款
- **批量操作**: 一键结算/撤销所有参与者
- **实时更新**: 基于 AJAX 的 UI 更新，无需刷新页面
- **智能状态**: 可视化付款状态指示器

### 📈 仪表板和分析
- **快速统计**: 已结算与未结算账单概览
- **债务跟踪**: 谁欠谁多少钱的清晰显示
- **个人面板**: 个人付款历史和债务情况

## 🚀 快速开始

### 环境要求
- Python 3.12+
- pip (Python 包管理器)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd 7769
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```

3. **安装依赖**
   ```bash
   # 方式1：从requirements.txt安装（推荐）
   pip install -r requirements.txt

   # 方式2：单独安装
   pip install flask flask-sqlalchemy flask-login werkzeug
   ```

4. **运行应用**
   ```bash
   # 直接启动（推荐）
   python3 app.py

   # 或使用虚拟环境
   python app.py
   ```

5. **在浏览器中打开**
   ```
   http://127.0.0.1:7769
   ```

## 🌐 网络访问

应用程序配置为监听所有网络接口（`host='0.0.0.0'`），允许同一网络内的其他设备访问。

### 本地访问
```
http://127.0.0.1:7769
```

### 局域网内其他设备访问
```
http://192.168.31.174:7769
```
*请替换为您的实际IP地址*

### 访问要求
- 设备必须连接到同一WiFi/局域网
- macOS防火墙必须允许Python接受传入连接
- 应用程序必须正在运行

### 查看本机IP地址
```bash
ifconfig | grep 'inet ' | grep -v '127.0.0.1'
```

## 👥 默认用户

系统预置了 4 个室友账户：

| 用户名 | 密码 | 显示名称 |
|--------|------|----------|
| roommate1 | password123 | 室友1 |
| roommate2 | password123 | 室友2 |
| roommate3 | password123 | 室友3 |
| roommate4 | password123 | 室友4 |

## 🏗️ 技术栈

- **后端**: Python Flask + SQLAlchemy ORM
- **前端**: Bootstrap 5 + 原生 JavaScript
- **数据库**: SQLite
- **文件上传**: Werkzeug
- **身份认证**: Flask-Login

## 📁 项目结构

```
7769/
├── app.py                 # Flask 主应用文件
├── models.py              # 数据库模型
├── templates/             # HTML 模板
│   ├── base.html         # 带导航的基础模板
│   ├── index.html        # 主仪表板
│   ├── login.html        # 登录页面
│   ├── add_bill.html     # 添加账单表单（含文件上传）
│   └── dashboard.html    # 个人面板
├── static/               # 静态资源
│   ├── css/style.css    # 自定义样式
│   ├── js/main.js       # JavaScript 功能
│   └── uploads/         # 上传的凭证文件
├── instance/            # Flask 实例文件夹
│   └── database.db      # SQLite 数据库
└── venv/               # Python 虚拟环境
```

## 🗄️ 数据库模式

### User（用户表）
- `id`: 主键
- `username`: 登录用户名（唯一）
- `password_hash`: 哈希密码
- `display_name`: UI 中显示的名称
- `created_at`: 账户创建时间

### Bill（账单表）
- `id`: 主键
- `payer_id`: 付款人（外键）
- `amount`: 账单金额
- `description`: 账单描述/类型
- `date`: 账单日期（用户选择）
- `participants`: 参与者 ID（逗号分隔）
- `is_settled`: 整体结算状态
- `created_at`: 账单创建时间

### Settlement（结算表）
- `id`: 主键
- `bill_id`: 关联账单（外键）
- `settler_id`: 付款用户（外键）
- `settled_amount`: 付款金额
- `settled_date`: 付款时间

### Receipt（凭证表）
- `id`: 主键
- `bill_id`: 关联账单（外键）
- `filename`: 原始文件名
- `file_type`: 文件类型（pdf/image）
- `file_size`: 文件大小（字节）
- `upload_date`: 上传时间

## 🔧 API 接口

- `GET /` - 主仪表板
- `GET /login` - 登录页面
- `POST /login` - 处理登录
- `GET /logout` - 用户登出
- `GET /add_bill` - 添加账单表单
- `POST /add_bill` - 处理新账单
- `GET /dashboard` - 个人面板
- `GET /settle_individual/<bill_id>/<user_id>` - 切换单人结算
- `GET /toggle_settlement/<bill_id>` - 切换全部结算
- `GET /api/debt_details` - 获取债务信息（JSON）
- `GET /api/receipt/<bill_id>` - 获取凭证信息（JSON）

## 🎯 使用指南

### 添加账单
1. 点击"添加账单"
2. 选择账单类型或选择"其它"进行自定义
3. 设置账单日期和金额
4. 选择需要分摊费用的参与者
5. 上传凭证文件（支持拖拽）
6. 查看费用分摊预览
7. 提交账单

### 管理结算
1. 在仪表板中找到账单
2. 点击特定室友的"结算"按钮进行单人结算
3. 使用"全部结算"进行批量操作
4. 状态更新立即显示，无需刷新页面

### 查看凭证
1. 点击任意账单的"查看凭证"
2. 多个文件将以标签页形式显示在模态框中
3. 使用下拉菜单下载单个文件
4. 点击全屏按钮获得更好的查看体验

## 🐛 故障排除

### 端口被占用
```bash
lsof -ti :7769 | xargs kill -9
```

### 数据库问题
数据库会在首次运行时自动初始化。如需重置：
```bash
rm instance/database.db
python3 app.py  # 将重新创建并添加默认用户
```

### 路径问题（已解决）
系统现在使用绝对路径配置，确保：
- 数据库文件：`{项目根目录}/instance/database.db`
- 上传文件：`{项目根目录}/static/uploads/receipts/`
- 无需依赖工作目录，支持任何IDE直接运行

### 文件上传问题
确保上传目录有正确的权限：
```bash
mkdir -p static/uploads/receipts
chmod 755 static/uploads/receipts
```

### 网络访问问题
```bash
# 检查防火墙状态（macOS）
sudo pfctl -s info

# 如果其他设备连接被拒绝：
# 1. 检查macOS系统偏好设置 > 安全性与隐私 > 防火墙
# 2. 允许Python接受传入连接
# 3. 验证设备在同一网络
# 4. 确认IP地址正确
```

## 🔄 最近更新

- ✅ **项目结构扁平化**: 从嵌套的`roommate-bills/`目录移动到根目录`7769/`
- ✅ **网络访问支持**: 配置`host='0.0.0.0'`支持局域网访问
- ✅ **错误消息改进**: 增强权限错误消息，提供更好的用户理解
- ✅ **路径配置修复**: 使用绝对路径配置，确保在任何目录下运行都正常工作
- ✅ **凭证文件访问**: 修复凭证文件404错误，完善上传路由路径处理
- ✅ **跨IDE兼容**: 完美支持VS Code、PyCharm等各种开发环境
- ✅ 多文件凭证上传，支持拖拽
- ✅ 实时 UI 更新，无需刷新页面
- ✅ 增强的账单类型选择系统
- ✅ 改进的模态凭证查看器
- ✅ 修复重复用户问题
- ✅ 添加全面的债务跟踪

## 📱 移动端支持

系统采用响应式设计，完全支持移动设备：
- 📱 触摸友好的界面
- 📱 适配手机屏幕的布局
- 📱 移动端拖拽上传支持

## 🏠 部署到家庭网络

### 树莓派部署

1. **传输文件**
   ```bash
   scp -r 7769/ pi@树莓派IP:/home/pi/
   ```

2. **安装依赖**
   ```bash
   ssh pi@树莓派IP
   cd /home/pi/7769
   python3 -m venv venv
   source venv/bin/activate
   pip install flask flask-sqlalchemy flask-login werkzeug
   ```

3. **创建系统服务**
   ```bash
   sudo nano /etc/systemd/system/roommate-bills.service
   ```

   内容：
   ```ini
   [Unit]
   Description=Roommate Bills App
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/7769
   Environment=PATH=/home/pi/7769/venv/bin
   ExecStart=/home/pi/7769/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   启用服务：
   ```bash
   sudo systemctl enable roommate-bills
   sudo systemctl start roommate-bills
   ```

## 🤝 贡献

1. Fork 本仓库
2. 创建功能分支
3. 进行更改
4. 充分测试
5. 提交 Pull Request

## ⚠️ 安全提醒

这是一个开发版应用，存在以下限制：
- 演示账户使用简单密码
- 未配置 HTTPS
- 适用于可信的家庭网络环境

生产环境部署时建议：
- 更改默认密码
- 实施 HTTPS
- 添加适当的身份认证
- 设置防火墙规则

## 📄 许可证

本项目采用 MIT 许可证开源。

---

**注意**: 本应用专为小型家庭使用设计。生产环境使用时应实施额外的安全措施。

## 🔄 最新更新记录 (2025-09-17)

### ⚠️ 关键Bug修复
- ✅ **文件删除Bug修复**: 修复删除账单时凭证文件残留的严重问题
- ✅ **账单编辑/删除功能**: 添加完整的账单管理及权限控制
- ✅ **权限系统**: 只有账单创建者才能编辑/删除账单
- ✅ **级联删除**: 正确删除所有关联文件和数据库记录

### 🔧 技术改进
- 修复文件存储路径不匹配导致的孤立文件问题
- 账单删除后自动清理空目录
- 增强删除日志记录
- 前端UI权限控制优化

### 📈 功能增强
- 删除账单前显示影响范围确认
- 编辑页面实时文件管理
- 更详细的成功/错误消息反馈
- 新增API端点支持单个凭证文件删除

### 🎯 用户体验提升
1. **管理账单**:
   - 编辑账单：点击您创建的账单上的"编辑"按钮
   - 删除账单：点击您创建的账单上的"删除"按钮
   - 仅账单创建者可见编辑/删除按钮
2. **安全性**:
   - 后端强制权限验证，防止恶意操作
   - 确认对话框防止误删除