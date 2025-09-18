# 室友记账系统 (Roommate Bills) - Claude 配置

这是一个用于室友之间分摊账单的 Flask Web 应用程序。

## 项目结构

```
7769/ (项目根目录)
├── app.py                 # Flask 主应用文件
├── models.py              # 数据库模型定义
├── templates/             # HTML 模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   ├── login.html        # 登录页（含密码重置功能）
│   ├── add_bill.html     # 添加账单页
│   ├── edit_bill.html    # 编辑账单页
│   ├── dashboard.html    # 个人面板
│   ├── admin.html        # 管理员面板
│   └── admin_logs.html   # 登录日志页面
├── static/               # 静态资源
│   ├── css/style.css    # 样式文件
│   ├── js/main.js       # JavaScript文件
│   └── uploads/         # 上传文件存储
│       └── receipts/    # 凭证文件存储目录
├── instance/            # Flask实例文件夹
│   └── database.db      # SQLite数据库
├── __pycache__/         # Python缓存文件
├── requirements.txt     # Python依赖
├── README.md           # 项目文档（英文）
├── README_CN.md        # 项目文档（中文）
├── CLAUDE.md           # Claude配置文档
├── .git/               # Git仓库
├── .gitignore          # Git忽略文件
└── .claude/            # Claude配置
```

## 技术栈

- **后端**: Python Flask + SQLAlchemy ORM
- **前端**: Bootstrap 5 + JavaScript
- **数据库**: SQLite
- **文件上传**: Werkzeug
- **身份认证**: Flask-Login

## 主要功能

1. **用户管理与安全**:
   - 登录/登出功能
   - 登录失败跟踪与密码重置系统
   - 动态密码提示（默认/自定义密码）
   - 登录日志记录与审计
2. **账单管理**:
   - 添加账单（支持多种类型和日期选择）
   - 编辑账单（仅创建者可编辑）
   - 删除账单（仅创建者可删除，支持级联删除）
   - 多文件凭证上传（拖拽支持）
   - 卡片式参与者选择界面（替代传统复选框）
   - 实时分摊计算和预览
   - 权限控制（创建者权限）
3. **结算管理**:
   - 单人结算/撤销
   - 全部结算/撤销
   - 实时UI更新（无刷新）
4. **凭证查看**: 模态框查看多文件凭证
5. **数据统计**: 债务详情和快速统计
6. **管理员功能**:
   - 用户管理面板（查看用户状态、密码状态）
   - 系统配置管理
   - 登录日志查看与筛选
   - 安全统计监控

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

### 方式2：使用依赖文件安装
```bash
# 安装所有依赖
pip install -r requirements.txt
# 然后启动
python3 app.py
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

第一个用户（室友1）具有管理员权限，可以访问管理面板进行系统管理。

## 数据库模型

- **User**: 用户表（新增安全字段：密码状态、登录跟踪、管理员权限等）
- **Bill**: 账单表
- **Settlement**: 结算记录表
- **Receipt**: 凭证文件表（支持多文件）
- **SystemConfig**: 系统配置表（键值对存储配置项）
- **LoginLog**: 登录日志表（记录所有登录尝试和安全审计）

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
- ✅ **项目结构扁平化**: 从嵌套的roommate-bills/目录移动到7769/根目录
- ✅ **网络访问支持**: 配置host='0.0.0.0'支持局域网访问
- ✅ **错误提示改进**: 权限错误消息更加详细和用户友好
- ✅ **账单删除功能**: 添加账单删除功能，支持级联删除所有关联数据
- ✅ **账单编辑功能**: 添加账单编辑功能，支持修改所有账单信息
- ✅ **权限控制**: 只有账单创建者才能编辑或删除账单
- ✅ **文件删除bug修复**: 修复凭证文件删除时路径错误导致文件残留的问题
- ✅ **级联删除**: 删除账单时正确删除所有关联的文件、数据库记录
- ✅ **UI现代化**: 实现卡片式参与者选择界面，提升用户体验
- ✅ **费用分摊预览**: 实时显示分摊计算结果和参与者状态
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

## 网络访问

应用程序配置为监听所有网络接口（`host='0.0.0.0'`），支持局域网访问：

### 本地访问
```
http://127.0.0.1:7769
```

### 局域网访问
```
http://192.168.1.100:7769  # 替换为您的实际IP地址
```

### 访问要求
- 设备必须连接到同一WiFi/局域网
- macOS防火墙需要允许Python接受传入连接
- 确保应用程序正在运行

### 获取当前IP地址
```bash
ifconfig | grep 'inet ' | grep -v '127.0.0.1'
```

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

### 网络访问问题
- 检查防火墙设置（macOS系统偏好设置 > 安全性与隐私 > 防火墙）
- 确保设备在同一网络
- 验证IP地址是否正确

### 文件访问404
- ✅ 已修复：使用正确的静态文件路径
- 凭证文件通过 `/uploads/` 路由访问
- 权限错误提示已改进："抱歉，您无权查看此凭证。只有参与该账单分摊的室友才能查看相关凭证文件。"

### 文件删除问题
- ✅ 已修复：修复凭证文件删除时路径不匹配的关键bug
- **问题**: 文件存储在 `/receipts/{bill_id}/filename` 但删除时使用 `/receipts/filename` 路径
- **解决**: 修正删除逻辑使用正确的子目录路径
- **影响**: 确保删除账单时能正确删除所有关联文件，避免孤立文件

## API 端点

### 核心路由
- `GET /` - 主仪表板页面
- `GET /login` - 登录页面（含密码重置功能）
- `POST /login` - 处理登录请求
- `GET /logout` - 用户登出
- `GET /add_bill` - 添加账单表单页面
- `POST /add_bill` - 处理新账单提交
- `GET /edit_bill/<bill_id>` - 编辑账单表单页面
- `POST /edit_bill/<bill_id>` - 处理账单编辑提交
- `POST /delete_bill/<bill_id>` - 删除账单及关联数据
- `GET /dashboard` - 个人面板页面

### 管理员路由
- `GET /admin` - 管理员面板（需管理员权限）
- `POST /admin_config` - 更新系统配置
- `GET /admin_logs` - 查看登录日志
- `POST /reset_password/<user_id>` - 重置用户密码为默认值

### 结算相关
- `GET /settle_individual/<bill_id>/<user_id>` - 切换单人结算状态
- `GET /toggle_settlement/<bill_id>` - 切换全部结算状态

### API接口
- `GET /api/debt_details` - 获取债务详情（JSON）
- `GET /api/receipt/<bill_id>` - 获取账单凭证信息（JSON）
- `DELETE /api/receipt/<receipt_id>` - 删除单个凭证文件

### 文件服务
- `GET /uploads/<path:filename>` - 提供凭证文件访问

## 最新bug修复 (2025-09-17)

### 关键文件删除bug修复
**问题描述**: 删除账单时，数据库记录被正确删除，但实际凭证文件未被删除，导致磁盘空间浪费。

**根本原因**:
- 文件上传时存储在子目录: `/static/uploads/receipts/{bill_id}/filename`
- 数据库只记录文件名: `filename`（不包含子目录路径）
- 删除时拼接错误路径: `/static/uploads/receipts/filename`（缺少bill_id子目录）

**修复方案**:
```python
# 修复前（错误）
file_path = os.path.join(UPLOAD_FOLDER, receipt.filename)

# 修复后（正确）
file_path = os.path.join(UPLOAD_FOLDER, str(bill_id), receipt.filename)
```

**附加改进**:
- 删除账单后自动清理空目录
- 添加详细的删除日志
- 确保级联删除的完整性

### 权限控制加强
- 只有账单创建者（付款人）可以编辑和删除账单
- 前端UI根据权限动态显示编辑/删除按钮
- 后端强制权限验证，防止恶意操作

### 用户体验改进
- 删除账单前弹出确认对话框，显示影响的记录数量
- 编辑页面支持实时文件管理
- 更详细的成功/错误消息反馈

## 最新安全功能更新 (2025-09-17)

### 🔐 登录安全系统
**新功能**: 将账户锁定机制改为用户友好的密码重置系统

**主要特性**:
- **登录失败跟踪**: 自动记录登录失败次数，默认5次后需要重置密码
- **自助密码重置**: 用户可在登录页面自行重置密码为默认值
- **动态密码提示**: 登录页面根据选中用户动态显示密码状态
  - 默认密码用户：显示"默认密码：password123"
  - 自定义密码用户：显示"请输入自定义密码"
- **智能UI更新**: 仅对需要重置密码的用户显示重置按钮

### 📊 管理员功能增强
**新增管理面板**:
- **用户管理**: 查看所有用户状态、密码状态、登录信息
- **系统配置**: 动态配置系统参数（如最大登录失败次数）
- **登录日志**: 完整的登录审计，支持筛选和分页
- **安全统计**: 实时统计成功/失败登录次数和成功率

### 🛡️ 安全改进
**替换账户锁定为密码重置**:
- **用户友好**: 不再锁定账户，用户可自助解决登录问题
- **保持安全**: 仍然跟踪登录失败次数，维护安全监控
- **简化管理**: 无需管理员干预解锁账户

### 📝 数据库扩展
**新增安全相关模型**:
- **SystemConfig**: 动态系统配置管理
- **LoginLog**: 详细登录日志记录（IP、浏览器、时间戳）
- **User模型扩展**: 新增安全字段（登录跟踪、密码状态、管理员权限）

## 最新UI改进更新 (2025-09-18)

### 🎨 登录界面现代化重设计
**重大UI更新**: 完全重新设计登录界面，提升用户体验和公平性

**主要改进**:
- **卡片式用户选择**: 从下拉框改为4个用户卡片，支持直观的点击选择
- **平滑选择动画**: 替换突兀的checkmark动画为温和的透明度和缩放过渡
- **自定义toggle开关**: 将"记住我"从复选框升级为专业的滑动开关
- **公平性优化**: 移除登录页面的管理员标识，避免室友间不公平感

### 🔧 技术实现细节
**卡片选择系统**:
```css
.user-card {
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);  // 选中时蓝色光晕
}

.selection-indicator {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 18px;
  height: 18px;
  opacity: 0 → 1;  // 平滑显示
  transform: scale(0.8) → scale(1);  // 温和缩放
}
```

**自定义Toggle开关**:
```css
.custom-toggle {
  width: 54px;
  height: 28px;
  .toggle-slider:before {
    transform: translateX(0) → translateX(26px);  // 滑块移动动画
  }
}
```

### 🎭 用户体验改进
**公平性优化**:
- 登录页面移除"管理员"徽章显示
- 导航栏"管理员"改为"系统管理"，更加中性
- 保持功能权限不变，仅优化显示文案

**交互优化**:
- 用户卡片支持悬停效果和焦点状态
- Toggle开关提供清晰的开/关视觉反馈
- 选择指示器使用小圆点代替大图标，更加精致

### 🔄 兼容性保证
**表单功能**:
- 保持原有的表单提交机制
- 隐藏的checkbox确保服务器端兼容
- 所有JavaScript交互向后兼容

**样式独立**:
- 自定义组件不依赖Bootstrap冲突样式
- 独立的CSS类避免样式污染
- 响应式设计适配移动端

### 📊 版本信息
- **当前版本**: v1.4
- **更新内容**: 登录界面现代化、公平性优化、自定义组件
- **兼容性**: 保持所有现有功能和API不变
- **状态**: 生产就绪，已完成完整初始化