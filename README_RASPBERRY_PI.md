# 🍓 室友记账系统 - 树莓派部署指南

专为树莓派优化的家庭记账网站，支持**下载即用**的快速部署体验。

## 🚀 一键部署（推荐）

```bash
# 1. 下载项目
git clone https://github.com/yourusername/7769.git
cd 7769

# 2. 运行一键部署脚本
bash deploy_raspberry.sh
```

**就是这么简单！** 脚本会自动完成：
- ✅ 系统环境检测（树莓派型号、Python版本、磁盘空间）
- ✅ 依赖安装（支持ARM架构）
- ✅ 环境配置（自动生成安全密钥）
- ✅ 系统服务创建（开机自启）
- ✅ 防火墙配置（开放7769端口）
- ✅ 应用启动和健康检查

## 📱 快速访问

部署完成后立即可用：

```
🏠 局域网访问: http://树莓派IP:7769
📱 手机访问: http://树莓派IP:7769
💻 电脑访问: http://树莓派IP:7769
```

**获取树莓派IP地址**：
```bash
hostname -I | cut -d' ' -f1
```

## 👥 默认账户

系统预置4个室友账户，开箱即用：

| 账户 | 密码 | 权限 | 显示名称 |
|------|------|------|----------|
| roommate1 | password123 | 管理员 | 室友1 |
| roommate2 | password123 | 普通用户 | 室友2 |
| roommate3 | password123 | 普通用户 | 室友3 |
| roommate4 | password123 | 普通用户 | 室友4 |

## 🔧 系统要求

### 最低配置
- **树莓派**: 树莓派2B或更新型号
- **系统**: Raspberry Pi OS (Debian-based)
- **Python**: 3.6+ （大多数树莓派系统自带）
- **内存**: 512MB RAM
- **存储**: 2GB可用空间（含操作系统）

### 推荐配置
- **树莓派**: 树莓派4B (2GB+)
- **SD卡**: Class 10或更高速度等级
- **网络**: 以太网连接（更稳定）

## 📦 手动安装（可选）

如果需要手动控制安装过程：

### 1. 环境准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip（通常已预装）
sudo apt install python3 python3-pip -y
```

### 2. 下载和配置
```bash
# 下载项目
git clone https://github.com/yourusername/7769.git
cd 7769

# 安装依赖
pip3 install -r requirements.txt --user

# 复制环境配置模板
cp .env.example .env

# 编辑配置（可选）
nano .env
```

### 3. 启动应用
```bash
# 方式1：直接启动（测试用）
python3 run.py

# 方式2：创建系统服务（推荐）
sudo cp roommate-bills.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable roommate-bills
sudo systemctl start roommate-bills
```

## 🛠️ 服务管理

### 基本命令
```bash
# 查看服务状态
sudo systemctl status roommate-bills

# 启动服务
sudo systemctl start roommate-bills

# 停止服务
sudo systemctl stop roommate-bills

# 重启服务
sudo systemctl restart roommate-bills

# 查看实时日志
sudo journalctl -u roommate-bills -f
```

### 健康检查
```bash
# 检查应用健康状态
curl http://localhost:7769/health

# 查看系统指标
curl http://localhost:7769/metrics
```

## 🔒 安全配置

### 生产环境建议
1. **修改默认密码**：首次登录后在管理面板修改所有用户密码
2. **更新密钥**：编辑`.env`文件中的`SECRET_KEY`
3. **启用HTTPS**：配置反向代理（如Nginx）
4. **防火墙设置**：限制只允许局域网访问

### 自动生成安全密钥
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

## 📊 存储管理

### SD卡保护模式
系统包含SD卡保护功能，减少写入频率：

```bash
# 在.env文件中启用
SD_CARD_PROTECTION=true
```

### 磁盘空间监控
- **自动检查**：应用启动时检查可用空间
- **警告阈值**：可用空间低于100MB时发出警告
- **上传限制**：单文件最大10MB（可配置）

### 备份配置
```bash
# 自动备份（每24小时）
AUTO_BACKUP_HOURS=24

# 备份保留数量
BACKUP_RETENTION_COUNT=7

# 备份存储路径
BACKUP_PATH=backups/
```

## 🌡️ 系统监控

### 温度监控
系统会自动监控树莓派CPU温度：

```bash
# 温度警告阈值
CPU_TEMP_WARNING=70

# 温度危险阈值
CPU_TEMP_CRITICAL=80
```

### 性能监控
- **启用指标收集**：`ENABLE_METRICS=true`
- **数据保留期**：30天
- **访问监控面板**：http://树莓派IP:7769/metrics

## 🔍 故障排除

### 常见问题

**Q: 服务启动失败？**
```bash
# 查看详细错误日志
sudo journalctl -u roommate-bills -n 50

# 检查端口占用
sudo lsof -i :7769

# 手动启动测试
cd /home/pi/7769
python3 run.py
```

**Q: 无法访问网站？**
```bash
# 检查服务状态
sudo systemctl status roommate-bills

# 检查防火墙
sudo ufw status

# 测试本地访问
curl http://localhost:7769
```

**Q: 磁盘空间不足？**
```bash
# 查看磁盘使用情况
df -h

# 清理日志文件
sudo journalctl --vacuum-time=7d

# 清理应用日志
rm -f /home/pi/7769/logs/*.log
```

**Q: Python版本过低？**
```bash
# 检查Python版本
python3 --version

# 在树莓派OS上升级Python（如需要）
sudo apt update && sudo apt install python3.8 python3.8-pip
```

### 重置应用
```bash
# 停止服务
sudo systemctl stop roommate-bills

# 删除数据库（重置所有数据）
rm -f /home/pi/7769/instance/database.db

# 清理上传文件
rm -rf /home/pi/7769/static/uploads/receipts/*

# 重启服务
sudo systemctl start roommate-bills
```

## 🔄 更新升级

### 更新应用
```bash
# 停止服务
sudo systemctl stop roommate-bills

# 拉取最新代码
cd /home/pi/7769
git pull origin main

# 更新依赖
pip3 install -r requirements.txt --user --upgrade

# 重启服务
sudo systemctl start roommate-bills
```

### 备份数据
```bash
# 备份数据库
cp /home/pi/7769/instance/database.db ~/backup_$(date +%Y%m%d).db

# 备份上传文件
tar -czf ~/uploads_backup_$(date +%Y%m%d).tar.gz /home/pi/7769/static/uploads/
```

## 📱 移动端使用

### 浏览器兼容性
- ✅ Safari (iOS)
- ✅ Chrome (Android)
- ✅ Firefox Mobile
- ✅ Edge Mobile

### PWA支持
应用支持添加到主屏幕，像原生应用一样使用：

1. 在手机浏览器中访问网站
2. 点击"添加到主屏幕"
3. 享受原生应用般的体验

## 🌐 网络配置

### 局域网访问
默认配置允许局域网内所有设备访问：

```bash
# 在.env文件中配置
HOST=0.0.0.0
PORT=7769
```

### 域名配置（可选）
如果有内网域名服务：

```bash
# 添加DNS记录
home-bills.local -> 树莓派IP地址
```

### 端口转发（可选）
如需外网访问，在路由器中配置端口转发：
- 外部端口：自定义
- 内部端口：7769
- 目标设备：树莓派IP

## 📈 性能优化

### 系统级优化
```bash
# 增加交换文件（如内存不足）
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # 设置CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# 优化SD卡性能
echo 'tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0' | sudo tee -a /etc/fstab
```

### 应用级优化
- **启用SD卡保护模式**：减少数据库写入频率
- **定期清理日志**：避免日志文件过大
- **限制上传文件大小**：保护存储空间

## 🎯 使用建议

### 家庭使用最佳实践
1. **设备命名**：为树莓派设置易记的主机名
2. **定期备份**：重要数据定期备份到外部存储
3. **网络稳定**：使用有线连接确保稳定性
4. **温度控制**：确保树莓派有良好散热
5. **电源稳定**：使用官方电源适配器

### 多用户协作
- **账户管理**：管理员定期检查用户状态
- **数据清理**：定期清理过期账单数据
- **安全审计**：查看登录日志确保安全

## 📞 技术支持

### 日志位置
- **系统日志**：`sudo journalctl -u roommate-bills`
- **应用日志**：`/home/pi/7769/logs/`
- **Web服务器日志**：应用内置日志系统

### 配置文件
- **环境配置**：`.env`
- **系统服务**：`/etc/systemd/system/roommate-bills.service`
- **应用配置**：`config.py`

### 数据位置
- **数据库**：`instance/database.db`
- **上传文件**：`static/uploads/receipts/`
- **备份文件**：`backups/`

---

**🎉 恭喜！您已成功部署家庭记账网站到树莓派！**

享受便捷的家庭财务管理体验吧！ 🏠💰📱