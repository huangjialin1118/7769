# Roommate Bills Management System

A Flask web application for managing and splitting bills between roommates with multi-file receipt upload and real-time settlement tracking.

[中文文档](README_CN.md) | English

## ✨ Features

### 📊 Bill Management
- **Smart Bill Types**: Predefined categories (utilities, groceries, food, etc.) with custom option
- **Date Selection**: Choose actual bill dates for better tracking
- **Card-based Selection**: Modern participant selection interface with intuitive user cards and real-time visual feedback
- **Real-time Calculation**: Automatic cost splitting with live preview and participant status display
- **Multi-participant**: Select which roommates to include in each bill
- **Edit Bills**: Modify existing bills (creator-only permission)
- **Delete Bills**: Remove bills with cascade deletion (creator-only permission)
- **Permission Control**: Only bill creators can edit or delete their bills

### 📎 Receipt Management
- **Multi-file Upload**: Upload multiple receipts per bill (images + PDFs)
- **Drag & Drop**: Intuitive drag-and-drop interface
- **File Management**: Preview, remove files before submission
- **Modal Viewer**: View receipts in enlarged modal with tabs for multiple files

### 💰 Settlement System
- **Individual Settlement**: Mark specific roommates as paid
- **Bulk Operations**: Settle/unsettled all participants at once
- **Real-time Updates**: AJAX-powered UI updates without page refresh
- **Smart Status**: Visual indicators for payment status

### 📈 Dashboard & Analytics
- **Quick Stats**: Overview of settled vs unsettled bills
- **Debt Tracking**: Who owes what to whom
- **Personal Panel**: Individual payment history and obligations

### 🔐 Security & User Management
- **Login Failure Tracking**: Automatic tracking of failed login attempts
- **Password Reset System**: User-friendly self-service password reset (no account locking)
- **Dynamic Password Hints**: Context-aware password field placeholders
- **Login Audit**: Comprehensive login logging with IP and browser tracking
- **Session Management**: Secure session handling with remember-me functionality

### 👨‍💼 Administrator Features
- **User Management Panel**: View all users, password status, and login statistics
- **System Configuration**: Dynamic system settings management
- **Login Logs**: Detailed audit trail with filtering and pagination
- **Security Dashboard**: Real-time statistics on login success/failure rates

## 🚀 Quick Start

### Prerequisites
- Python 3.6+ (compatible with Raspberry Pi and ARM architectures)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 7769
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   # Option 1: Install from requirements.txt (recommended)
   pip install -r requirements.txt

   # Option 2: Install individually
   pip install flask flask-sqlalchemy flask-login werkzeug
   ```

4. **Run the application**
   ```bash
   # Direct startup (recommended)
   python3 app.py

   # Or using virtual environment
   python app.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:7769
   ```

## 🌐 Network Access

The application is configured to listen on all network interfaces (`host='0.0.0.0'`), allowing access from other devices on the same network.

### Local Access
```
http://127.0.0.1:7769
```

### LAN Access from Other Devices
```
http://192.168.31.174:7769
```
*Replace with your actual IP address*

### Access Requirements
- Devices must be connected to the same WiFi/LAN
- macOS firewall must allow Python to accept incoming connections
- Application must be running

### Find Your IP Address
```bash
ifconfig | grep 'inet ' | grep -v '127.0.0.1'
```

## 👥 Default Users

The system comes with 4 pre-configured roommate accounts:

| Username | Password | Display Name | Role |
|----------|----------|--------------|------|
| roommate1 | password123 | 室友1 | Admin |
| roommate2 | password123 | 室友2 | User |
| roommate3 | password123 | 室友3 | User |
| roommate4 | password123 | 室友4 | User |

*The first user (室友1) has administrator privileges for system management.*

## 🏗️ Tech Stack

- **Backend**: Python Flask + SQLAlchemy ORM
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Database**: SQLite
- **File Upload**: Werkzeug
- **Authentication**: Flask-Login

## 📁 Project Structure

```
7769/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Main dashboard
│   ├── login.html        # Login page
│   ├── add_bill.html     # Add bill form with file upload
│   ├── edit_bill.html    # Edit bill form with file management
│   └── dashboard.html    # Personal dashboard
├── static/               # Static assets
│   ├── css/style.css    # Custom styles
│   ├── js/main.js       # JavaScript functionality
│   └── uploads/         # Uploaded receipt files
├── instance/            # Flask instance folder
│   └── database.db      # SQLite database
└── venv/               # Python virtual environment
```

## 🗄️ Database Schema

### User
- `id`: Primary key
- `username`: Unique username for login
- `password_hash`: Hashed password
- `display_name`: Display name shown in UI
- `created_at`: Account creation timestamp
- `is_default_password`: Whether user is using default password
- `is_admin`: Administrator privileges flag
- `last_login`: Last successful login timestamp
- `login_attempts`: Failed login attempt counter
- `is_active`: Account activation status

### Bill
- `id`: Primary key
- `payer_id`: User who paid the bill (Foreign Key)
- `amount`: Bill amount
- `description`: Bill description/type
- `date`: Bill date (user-selected)
- `participants`: Comma-separated participant IDs
- `is_settled`: Overall settlement status
- `created_at`: Bill creation timestamp

### Settlement
- `id`: Primary key
- `bill_id`: Associated bill (Foreign Key)
- `settler_id`: User who made payment (Foreign Key)
- `settled_amount`: Amount paid
- `settled_date`: Payment timestamp

### Receipt
- `id`: Primary key
- `bill_id`: Associated bill (Foreign Key)
- `filename`: Original filename
- `file_type`: File type (pdf/image)
- `file_size`: File size in bytes
- `upload_date`: Upload timestamp

### SystemConfig
- `id`: Primary key
- `key`: Configuration key (unique)
- `value`: Configuration value
- `description`: Human-readable description
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### LoginLog
- `id`: Primary key
- `user_id`: Associated user (Foreign Key, nullable)
- `username`: Username attempted (preserved even if user deleted)
- `ip_address`: Client IP address
- `user_agent`: Browser/client information
- `login_time`: Attempt timestamp
- `success`: Whether login succeeded
- `failure_reason`: Reason for failure (if applicable)

## 🔧 API Endpoints

### Core Routes
- `GET /` - Main dashboard
- `GET /login` - Login page (with password reset functionality)
- `POST /login` - Process login
- `GET /logout` - Logout user
- `GET /add_bill` - Add bill form
- `POST /add_bill` - Process new bill
- `GET /edit_bill/<bill_id>` - Edit bill form (creator-only)
- `POST /edit_bill/<bill_id>` - Process bill edit (creator-only)
- `POST /delete_bill/<bill_id>` - Delete bill with cascade deletion (creator-only)
- `GET /dashboard` - Personal dashboard

### Settlement Routes
- `GET /settle_individual/<bill_id>/<user_id>` - Toggle individual settlement
- `GET /toggle_settlement/<bill_id>` - Toggle all settlements

### Administrator Routes (Admin-only)
- `GET /admin` - Administrator panel
- `POST /admin_config` - Update system configuration
- `GET /admin_logs` - View login logs with filtering
- `POST /reset_password/<user_id>` - Reset user password to default

### API Routes
- `GET /api/debt_details` - Get debt information (JSON)
- `GET /api/receipt/<bill_id>` - Get receipt information (JSON)
- `DELETE /api/receipt/<receipt_id>` - Delete individual receipt file

## 🎯 Usage Guide

### Adding a Bill
1. Click "添加账单" (Add Bill)
2. Select bill type or choose "其它" (Other) for custom
3. Set bill date and amount
4. Select participants who should split the cost
5. Upload receipt files (drag & drop supported)
6. Review the cost split preview
7. Submit the bill

### Managing Bills
1. **Edit Bill**: Click the "编辑" (Edit) button on bills you created
   - Modify amount, date, description, and participants
   - Add or remove receipt files
   - Changes are saved with real-time preview
2. **Delete Bill**: Click the "删除" (Delete) button on bills you created
   - Confirmation dialog shows impact (settlements, receipts)
   - Permanently removes bill, settlements, and all receipt files
   - Only available to bill creators

### Managing Settlements
1. From the dashboard, find the bill
2. Click individual "结算" (Settle) buttons for specific roommates
3. Use "全部结算" (Settle All) for bulk operations
4. Status updates appear instantly without page refresh

### Viewing Receipts
1. Click "查看凭证" (View Receipt) on any bill
2. Multiple files appear as tabs in the modal
3. Use download dropdown for individual file downloads
4. Click fullscreen button for better viewing

### Password Reset (Self-Service)
1. If you exceed maximum login attempts (default: 5), a reset button appears
2. Click "重置密码" (Reset Password) button on login page
3. Your password resets to "password123" automatically
4. Login with the default password
5. Change to a custom password after successful login

### Administrator Features (Admin Users Only)
1. **User Management**:
   - View all user accounts and their status
   - See password status (default/custom)
   - Monitor login attempts and last login times
   - View security statistics

2. **System Configuration**:
   - Adjust maximum login attempts
   - Configure other system parameters
   - Real-time configuration updates

3. **Login Logs**:
   - View complete login audit trail
   - Filter by username or success/failure
   - Paginated results for large datasets
   - Export functionality for security analysis

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -ti :7769 | xargs kill -9
```

### Database Issues
The database auto-initializes on first run. If you need to reset:
```bash
rm instance/database.db
python3 app.py  # Will recreate with default users
```

### Path Issues (Resolved)
The system now uses absolute path configuration, ensuring:
- Database file: `{project_root}/instance/database.db`
- Upload files: `{project_root}/static/uploads/receipts/`
- No dependency on working directory, supports any IDE direct execution

### File Upload Issues
Ensure the uploads directory has proper permissions:
```bash
mkdir -p static/uploads/receipts
chmod 755 static/uploads/receipts
```

### Network Access Issues
```bash
# Check firewall status (macOS)
sudo pfctl -s info

# If connection refused from other devices:
# 1. Check macOS System Preferences > Security & Privacy > Firewall
# 2. Allow Python to accept incoming connections
# 3. Verify devices are on same network
# 4. Confirm IP address is correct
```

## 🔄 Recent Updates

### Latest UI Modernization (2025-09-18)
- ✅ **Card-style Login Interface**: Replaced dropdown user selection with intuitive user cards
- ✅ **Custom Toggle Switch**: Upgraded "Remember Me" from checkbox to professional sliding toggle
- ✅ **Smooth Animation System**: Replaced abrupt checkmark with gentle fade and scale transitions
- ✅ **Fairness Optimization**: Removed administrator badges from login for equal user experience
- ✅ **Modern Selection Indicators**: Elegant circular indicator with blue glow effect

### Previous Major Updates
- ✅ **Project Structure Flattened**: Moved from nested `roommate-bills/` to root `7769/` directory
- ✅ **Network Access Added**: Configured `host='0.0.0.0'` for LAN access support
- ✅ **Error Messages Improved**: Enhanced permission error messages for better user understanding
- ✅ **Path Configuration Fixed**: Absolute path configuration ensures consistent operation regardless of execution directory
- ✅ **Receipt File Access**: Fixed 404 error for receipt files by correcting upload route path handling
- ✅ **Cross-IDE Compatibility**: Works seamlessly with VS Code, PyCharm, and other IDEs
- ✅ **Bill Edit/Delete Features**: Added comprehensive bill management with permission control
- ✅ **Critical File Deletion Bug Fix**: Fixed orphaned receipt files issue during bill deletion
- ✅ **Permission System**: Only bill creators can edit/delete their bills
- ✅ **Cascade Deletion**: Properly delete all associated files and database records
- ✅ Multi-file receipt upload with drag & drop
- ✅ Real-time UI updates without page refresh
- ✅ Enhanced bill type selection system
- ✅ Improved modal receipt viewer
- ✅ Fixed duplicate user issues
- ✅ Added comprehensive debt tracking

## 🔧 Latest Bug Fixes (2025-09-17)

### Critical File Deletion Bug Fix
**Issue**: When deleting bills, database records were correctly removed but actual receipt files remained on disk, causing storage waste.

**Root Cause**:
- Files uploaded to subdirectories: `/static/uploads/receipts/{bill_id}/filename`
- Database only stores filename: `filename` (without subdirectory path)
- Deletion logic used wrong path: `/static/uploads/receipts/filename` (missing bill_id subdirectory)

**Solution**:
```python
# Before (incorrect)
file_path = os.path.join(UPLOAD_FOLDER, receipt.filename)

# After (correct)
file_path = os.path.join(UPLOAD_FOLDER, str(bill_id), receipt.filename)
```

**Additional Improvements**:
- Automatic cleanup of empty directories after bill deletion
- Enhanced deletion logging for better debugging
- Ensures complete cascade deletion integrity

### Permission Control Enhancement
- Only bill creators (payers) can edit and delete bills
- Frontend UI dynamically shows edit/delete buttons based on permissions
- Backend enforces permission validation to prevent malicious operations

### User Experience Improvements
- Confirmation dialog before bill deletion showing impact statistics
- Edit page supports real-time file management
- More detailed success/error message feedback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## ⚠️ Security Notice

This is a development application with the following limitations:
- Uses simple passwords for demo accounts
- No HTTPS configuration
- Designed for trusted home network use

For production deployment, consider:
- Changing default passwords
- Implementing HTTPS
- Adding proper authentication
- Setting up firewall rules

## 📄 License

This project is open source and available under the MIT License.

---

**Note**: This application is designed for small household use. For production environments, additional security measures should be implemented.