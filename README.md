# Roommate Bills Management System

A Flask web application for managing and splitting bills between roommates with multi-file receipt upload and real-time settlement tracking.

[中文文档](README_CN.md) | English

## ✨ Features

### 📊 Bill Management
- **Smart Bill Types**: Predefined categories (utilities, groceries, food, etc.) with custom option
- **Date Selection**: Choose actual bill dates for better tracking
- **Real-time Calculation**: Automatic cost splitting with live preview
- **Multi-participant**: Select which roommates to include in each bill

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

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd roommate-bills
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
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

## 👥 Default Users

The system comes with 4 pre-configured roommate accounts:

| Username | Password | Display Name |
|----------|----------|--------------|
| roommate1 | password123 | 室友1 |
| roommate2 | password123 | 室友2 |
| roommate3 | password123 | 室友3 |
| roommate4 | password123 | 室友4 |

## 🏗️ Tech Stack

- **Backend**: Python Flask + SQLAlchemy ORM
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Database**: SQLite
- **File Upload**: Werkzeug
- **Authentication**: Flask-Login

## 📁 Project Structure

```
roommate-bills/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Main dashboard
│   ├── login.html        # Login page
│   ├── add_bill.html     # Add bill form with file upload
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

## 🔧 API Endpoints

- `GET /` - Main dashboard
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /logout` - Logout user
- `GET /add_bill` - Add bill form
- `POST /add_bill` - Process new bill
- `GET /dashboard` - Personal dashboard
- `GET /settle_individual/<bill_id>/<user_id>` - Toggle individual settlement
- `GET /toggle_settlement/<bill_id>` - Toggle all settlements
- `GET /api/debt_details` - Get debt information (JSON)
- `GET /api/receipt/<bill_id>` - Get receipt information (JSON)

## 🎯 Usage Guide

### Adding a Bill
1. Click "添加账单" (Add Bill)
2. Select bill type or choose "其它" (Other) for custom
3. Set bill date and amount
4. Select participants who should split the cost
5. Upload receipt files (drag & drop supported)
6. Review the cost split preview
7. Submit the bill

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

## 🔄 Recent Updates

- ✅ **Path Configuration Fixed**: Absolute path configuration ensures consistent operation regardless of execution directory
- ✅ **Receipt File Access**: Fixed 404 error for receipt files by correcting upload route path handling
- ✅ **Cross-IDE Compatibility**: Works seamlessly with VS Code, PyCharm, and other IDEs
- ✅ Multi-file receipt upload with drag & drop
- ✅ Real-time UI updates without page refresh
- ✅ Enhanced bill type selection system
- ✅ Improved modal receipt viewer
- ✅ Fixed duplicate user issues
- ✅ Added comprehensive debt tracking

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