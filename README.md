# CameraTimeCard
Complete electronic time clock control system using facial recognition with OpenCV and face_recognition, integrated with a Flask backend for data storage.

# Electronic Time Clock Control System

Complete electronic time clock control system using facial recognition with OpenCV and face_recognition, integrated with a Flask backend for data storage.

## Features

- Real-time facial recognition with OpenCV and face_recognition
- Automatic entry/exit registration with cooldown control
- Complete Flask backend with REST API and SQLite database
- Intuitive visual interface using OpenCV with real-time information
- New employee registration via camera
- Database management with reports and statistics
- Security control

## Advanced Features

- Customizable configuration via custom_config.py file
- Work schedule control with validation
- Cooldown system to prevent duplicate registrations
- Automatic backup of recognition data
- Detailed logs for troubleshooting
- Webhook notifications (optional)
- Unknown face saving for auditing
- Encoding cache for better performance
- Multiple photos per employee for greater accuracy

Technologies Used

Python 3.7+ as main language
OpenCV for video capture and processing
face_recognition for facial recognition
Flask for backend API
SQLite for database
Requests for HTTP communication


## Prerequisites

- Python 3.7 or higher
- Camera connected to computer
- Operating system: Linux (Ubuntu/Debian), Windows or macOS
- Minimum 4GB RAM recommended
- 1GB free disk space

### System Dependencies (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip cmake
sudo apt-get install libopencv-dev python3-opencv
sudo apt-get install libboost-python-dev
```

## Installation

### 1. Clone/Download files

Make sure you have all files in one folder:
- `facial_recognition_system.py` - Main system
- `backend.py` - Flask server
- `requirements.txt` - Dependencies
- `setup.sh` - Configuration script

### 2. Automatic setup

```bash
# Download and run installer
chmod +x complete_installer.sh
./complete_installer.sh
```

### 3. Manual setup (alternative)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate # Linux/Mac
# or
venv\Scripts\activate # Windows

# Install dependencies
pip install -r requirements.txt
```

## How to Use

### 1. Start complete system

```bash
./start_system.sh
```

### 2. Or start components separately

**Backend (Terminal 1)**
```bash
source venv/bin/activate
python backend.py
```

**Recognition System (Terminal 2)**
```bash
source venv/bin/activate
python facial_recognition_system.py
```

### 3. Register new employee

```bash
python register_employee.py 5 12345 "John Silva"
```

## System Interface

### Main Menu

1. Start recognition - Activates camera for recognition
2. Register new employee - Register employee via camera
3. Exit - Close system

### During Recognition

- **Green rectangle**: Recognized employee
- **Red rectangle**: Unregistered person
- **Press 'q'**: Exit recognition

## Backend API

### Available Endpoints

#### Register Time Entry

```http
POST /api/timecard
Content-Type: application/json

{
  "employee_id": "12345",
  "employee_name": "John Silva",
  "timestamp": "2024-01-01T10:30:00"
}
```

#### List All Time Entries

```http
GET /api/timecards?limit=50&start_date=2024-01-01&end_date=2024-01-31
```

#### Employee Time Entries

```http
GET /api/employee/12345/timecards
```

#### Employee Current Status

```http
GET /api/employee/12345/status
```

#### List Employees

```http
GET /api/employees
```

#### Health Check

```http
GET /api/health
```

## Data Structure

### TimeCard (Time Entry)

```json
{
  "id": 1,
  "employee_id": "12345",
  "employee_name": "John Silva",
  "timestamp": "2024-01-01T10:30:00",
  "entry_type": "entrada",
  "recognition_method": "facial",
  "created_at": "2024-01-01T10:30:05"
}
```

### Employee

```json
{
  "id": "12345",
  "name": "John Silva",
  "created_at": "2024-01-01T09:00:00"
}
```

## API Documentation

### Authentication

All API endpoints support optional authentication:

```http
Authorization: Bearer your_api_token_here
```

### Main Endpoints

#### Register Time Entry

```http
POST /api/timecard
Content-Type: application/json

{
  "employee_id": "12345",
  "employee_name": "John Silva",
  "timestamp": "2024-01-01T10:30:00",
  "entry_type": "entry"
}
```

#### Get Employee Status

```http
GET /api/employee/12345/status
```

Response:
```json
{
  "employee_id": "12345",
  "name": "John Silva",
  "status": "checked_in",
  "last_entry": "2024-01-01T09:00:00",
  "total_hours_today": 8.5
}
```

#### Generate Reports

```http
GET /api/reports/daily?date=2024-01-01
GET /api/reports/weekly?week=2024-W01
GET /api/reports/monthly?month=2024-01
```

## Database Management

### Using db_manager.py

```bash
# List all employees
python db_manager.py employees --list

# Add employee
python db_manager.py employees --add --id 12345 --name "John Silva"

# Generate report
python db_manager.py reports --daily --date 2024-01-01

# Backup database
python db_manager.py backup --create

# Restore database
python db_manager.py backup --restore backup_2024-01-01.db
```

### Database Schema

#### Employees Table
```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    department TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

#### Timecards Table
```sql
CREATE TABLE timecards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    entry_type TEXT NOT NULL,
    recognition_method TEXT DEFAULT 'facial',
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

## Testing

### Run Complete Test Suite

```bash
python test_system.py --all
```

### Individual Tests

```bash
# Test camera
python test_system.py --camera

# Test recognition
python test_system.py --recognition

# Test API
python test_system.py --api

# Test database
python test_system.py --database
```

## Troubleshooting

### Common Issues

#### Camera Not Found
```bash
# Check available cameras
ls /dev/video*

# Test camera manually
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error')"
```

#### Recognition Accuracy Issues
- Improve lighting conditions
- Adjust `FACE_RECOGNITION_TOLERANCE` (lower = more strict)
- Register multiple photos per employee
- Clean camera lens

#### Performance Issues
- Reduce `FRAME_WIDTH` and `FRAME_HEIGHT`
- Increase `FACE_DETECTION_SCALE`
- Enable encoding cache
- Use fewer recognition threads

#### API Connection Issues
- Check if Flask server is running on port 5000
- Verify `BACKEND_URL` in configuration
- Check firewall settings
- Review API logs

### Log Files

```bash
# System logs
tail -f logs/system.log

# API logs
tail -f logs/api.log

# Recognition logs
tail -f logs/recognition.log

# Error logs
tail -f logs/error.log
```

## Security Considerations

1. **Data Protection**: Facial encodings are stored locally and encrypted
2. **Network Security**: Use HTTPS in production environments
3. **Access Control**: Implement proper authentication for API endpoints
4. **Audit Trail**: All activities are logged with timestamps
5. **Backup Security**: Encrypted backups with rotation policy
6. **Privacy Compliance**: Follows GDPR guidelines for biometric data

## Performance Optimization

### Hardware Recommendations

- **CPU**: Multi-core processor (Intel i5 or AMD Ryzen 5 minimum)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: SSD recommended for better database performance
- **Camera**: 720p minimum, 1080p recommended

### Software Optimization

```python
# Optimize for speed
FACE_DETECTION_SCALE = 0.5  # Faster detection
RECOGNITION_THREAD_COUNT = 4  # More parallel processing
ENCODING_CACHE_SIZE = 2000  # Larger cache

# Optimize for accuracy
FACE_RECOGNITION_TOLERANCE = 0.4  # More strict matching
FACE_DETECTION_SCALE = 0.25  # More detailed detection
```

## Deployment

### Production Deployment

```bash
# Create production configuration
cp custom_config.py production_config.py

# Edit production settings
nano production_config.py

# Deploy with production config
python facial_recognition_advanced.py --config production_config.py
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "facial_recognition_advanced.py"]
```

## Configuration

### config.py File

```python
# Camera Settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Recognition Settings
FACE_RECOGNITION_TOLERANCE = 0.6
RECOGNITION_COOLDOWN = 10  # seconds
MAX_FACES_PER_FRAME = 5

# Backend Settings
BACKEND_URL = "http://localhost:5000/api"
API_TIMEOUT = 30

# Advanced Features
ENABLE_WEBHOOK = False
WEBHOOK_URL = ""
SAVE_UNKNOWN_FACES = True
ENABLE_BACKUP = True
BACKUP_INTERVAL = 3600  # seconds
```

### You can customize the system behavior by editing custom_config.py:


```python
WORK_HOURS = {
    'start': '08:00',
    'end': '18:00',
    'lunch_start': '12:00',
    'lunch_end': '13:00'
}

# Performance Settings
ENCODING_CACHE_SIZE = 1000
FACE_DETECTION_SCALE = 0.25
RECOGNITION_THREAD_COUNT = 2

# Security Settings
MAX_LOGIN_ATTEMPTS = 3
SESSION_TIMEOUT = 3600
REQUIRE_ADMIN_AUTH = True
```

### Performance Adjustments

- **Recognition tolerance**: Lower values = more strict
- **Cooldown**: Minimum time between records for same employee
- **Camera resolution**: Lower resolution = better performance

## Troubleshooting

### Common Problems

#### 1. Camera not found

```bash
# Check available cameras
ls /dev/video*

# Adjust camera index in code
CAMERA_INDEX = 1  # Try different values
```

#### 2. Error installing dlib

```bash
# Ubuntu/Debian
sudo apt-get install build-essential cmake
sudo apt-get install libgtk-3-dev libboost-python-dev

# Install dlib separately
pip install dlib
```

#### 3. Inaccurate recognition

- Adjust `FACE_RECOGNITION_TOLERANCE`
- Improve environment lighting
- Re-register employee with better quality

#### 4. Backend doesn't connect

- Check if port 5000 is free
- Confirm backend URL in system
- Check error logs

### System Logs

```bash
# Check logs
tail -f logs/system.log

# Backend logs
tail -f flask.log
```

## File Structure

```
sistema-ponto/
├── facial_recognition_system.py - Basic recognition system
├── facial_recognition_advanced.py - Advanced version with more features
├── backend.py - Flask server with complete API
├── advanced_config.py - Customizable configuration system
├── db_manager.py - Database management utility
├── test_system.py - Complete testing script
├── complete_installer.sh - Automatic installer
├── requirements.txt - Python dependencies
├── README.md                    # This file
├── data/
│   ├── face_encodings.pkl       # Registered face data
│   └── timecard.db              # SQLite database
├── logs/
│   └── system.log               # System logs
├── employee_photos/             # Employee photos (optional)
└── venv/                        # Python virtual environment
```

## Security Considerations

1. **Biometric data**: Facial encodings are stored locally
2. **HTTPS**: Configure HTTPS in production
3. **Authentication**: Add API authentication for corporate environments
4. **Backup**: Regular backup of `face_encodings.pkl` file

## Future Improvements

- Web administrative interface
- PDF time reports
- Active Directory integration
- Multiple cameras
- Alternative QR Code recognition
- Real-time notifications
- Real-time dashboard

## Support

For technical issues:

1. Check logs in `logs/` directory
2. Run system diagnostics: `python test_system.py --diagnostics`
3. Review configuration: `python advanced_config.py --check`
4. Contact support with error details
5. Confirm installed dependencies
6. Test camera separately
7. Check network connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request


## License

This project is provided as-is, for educational and commercial use.

Developed using Python, OpenCV and Flask
