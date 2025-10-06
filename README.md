# 🎓 QR Attendance Agent

**Professional-grade AI-powered attendance automation system for NSBM University**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.0--Flash-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

- **AI-Powered QR Conversion**: Convert expired QR codes using Gemini 2.0 Flash
- **Evening Session Generation**: Automatically create evening QR codes from morning sessions
- **Automated Attendance Marking**: Web scraping automation with Selenium
- **Airtable Integration**: Store all records in organized database
- **Professional UI**: Modern dark-themed responsive interface
- **Real-time Processing**: Live status updates and result display
- **Screenshot Verification**: Capture confirmation for audit trail
- **Industrial Logging**: Comprehensive error tracking and monitoring

## 📁 Project Structure

```
qr-attendance-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── routes.py            # API endpoints
│   │   ├── config.py            # Configuration management
│   │   ├── logging_config.py    # Logging setup
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── services/
│   │   │   ├── gemini_service.py     # AI QR conversion
│   │   │   ├── airtable_service.py   # Database operations
│   │   │   ├── qr_generator.py       # QR code image generation
│   │   │   ├── scraping_service.py   # Web automation
│   │   │   └── qr_service.py         # Main orchestrator
│   │   └── utils/
│   │       └── helpers.py       # Utility functions
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Main UI
│   ├── css/
│   │   └── style.css           # Styling
│   └── js/
│       └── app.js              # Frontend logic
├── logs/                       # Application logs
├── qr_codes/                   # Generated QR images
├── screenshots/                # Confirmation screenshots
├── .env                        # Environment variables
├── .env.example               # Environment template
├── .gitignore
├── Procfile                   # Railway deployment
├── railway.json               # Railway configuration
├── start.sh                   # Startup script
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google Chrome/Chromium
- Gemini API Key
- Airtable API Key

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/qr-attendance-agent.git
cd qr-attendance-agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r backend/requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the application**
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

```

6. **Access the application**
```
Frontend: http://localhost:8000/app
API Docs: http://localhost:8000/docs
Health Check: http://localhost:8000/health
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=QR_Attendance

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# NSBM Login Credentials
DEFAULT_USERNAME=your_nsbm_username
DEFAULT_PASSWORD=your_nsbm_password

# Directory Configuration
QR_CODE_DIR=qr_codes
SCREENSHOT_DIR=screenshots
LOG_DIR=logs
```

### Getting API Keys

**Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and paste into `.env`

**Airtable API Key:**
1. Visit [Airtable Account](https://airtable.com/account)
2. Generate a personal access token
3. Create a base and table named "QR_Attendance"
4. Copy Base ID from the base URL
5. Add both to `.env`

## 🚂 Railway Deployment

### Step 1: Prepare Your Project

1. Ensure all files are committed to Git:
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Push to GitHub:
```bash
git remote add origin https://github.com/yourusername/qr-attendance-agent.git
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to [Railway.app](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the configuration

### Step 3: Configure Environment Variables

In Railway Dashboard:
1. Go to your project → Variables
2. Add all variables from `.env.example`
3. Click "Deploy" to redeploy with new variables

### Step 4: Configure Domain (Optional)

1. Go to Settings → Domains
2. Click "Generate Domain" or add custom domain
3. Your app will be live at the generated URL

### Important Railway Notes

- **start.sh** handles Chrome installation automatically
- **Procfile** defines the start command
- **railway.json** configures build and deploy settings
- Railway provides a Nixpacks environment with all system dependencies

## 📚 API Documentation

### Endpoints

#### Convert Expired QR
```http
POST /api/convert-expired-qr
Content-Type: application/json

{
  "qr_link": "https://students.nsbm.ac.lk/attendence/index.php?id=52202002751_84783",
  "module_name": "Software Engineering",
  "username": "optional_username",
  "password": "optional_password"
}
```

#### Create Evening QR
```http
POST /api/create-evening-qr
Content-Type: application/json

{
  "morning_qr_link": "https://students.nsbm.ac.lk/attendence/index.php?id=52658402247_84785",
  "module_name": "Software Engineering",
  "username": "optional_username",
  "password": "optional_password"
}
```

#### Health Check
```http
GET /health
```

#### Download Files
```http
GET /api/download/qr/{filename}
GET /api/download/screenshot/{filename}
```

## 🎨 Frontend Features

- **Dual Mode Operation**: Switch between expired QR conversion and evening QR creation
- **Real-time Status Updates**: Live processing feedback
- **Instant Download**: Download generated QR codes and screenshots
- **Copy to Clipboard**: One-click QR link copying
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Theme**: Professional modern UI

## 🔐 Security

- Credentials stored in environment variables
- HTTPS recommended for production
- Input validation on all endpoints
- Error messages sanitized
- No sensitive data in logs

## 🧪 Testing

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

### Test QR Conversion
```bash
curl -X POST http://localhost:8000/api/convert-expired-qr \
  -H "Content-Type: application/json" \
  -d '{
    "qr_link": "https://students.nsbm.ac.lk/attendence/index.php?id=52202002751_84783",
    "module_name": "Test Module"
  }'
```

## 📊 Monitoring

### Logs

Application logs are stored in the `logs/` directory:
- `app_YYYYMMDD.log` - General application logs
- `error_YYYYMMDD.log` - Error-specific logs

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical issues

## 🛠️ Troubleshooting

### Common Issues

**Chrome Driver Issues:**
```bash
# Manually install ChromeDriver
pip install webdriver-manager --upgrade
```

**Port Already in Use:**
```bash
# Change port in .env or use different port
uvicorn app.main:app --port 8001
```

**Selenium Timeout:**
- Check internet connection
- Increase timeout in `scraping_service.py`
- Verify NSBM website is accessible

**Gemini API Errors:**
- Verify API key is correct
- Check API quota limits
- Ensure model name is correct

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Your Name** - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- NSBM Green University for the attendance system
- Google Gemini AI for intelligent QR conversion
- FastAPI for the amazing web framework
- Airtable for database services

## 📞 Support

For support, email your-email@example.com or open an issue on GitHub.

---

**Made with ❤️ for NSBM Students**