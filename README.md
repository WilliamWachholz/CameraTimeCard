# CameraTimeCard
Complete electronic time clock control system using facial recognition with OpenCV and face_recognition, integrated with a Flask backend for data storage.

# Electronic Time Clock Control System

Complete electronic time clock control system using facial recognition with OpenCV and face_recognition, integrated with a Flask backend for data storage.

## Features

- Real-time facial recognition using camera
- Automatic entry/exit registration with cooldown
- Flask backend with REST API
- SQLite database for storage
- Visual interface with OpenCV
- New employee registration via camera
- Duplicate control and validations

## Prerequisites

- Python 3.7 or higher
- Camera connected to computer
- Operating system: Linux (Ubuntu/Debian), Windows or macOS

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
chmod +x setup.sh
./setup.sh
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

## Configuration

### config.py File

```python
# Backend
BACKEND_URL = "http://localhost:5000/api"

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Recognition
FACE_RECOGNITION_TOLERANCE = 0.6
RECOGNITION_COOLDOWN = 10  # seconds
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
├── facial_recognition_system.py # Main system
├── backend.py                   # Flask server
├── requirements.txt             # Dependencies
├── setup.sh                     # Configuration script
├── start_system.sh              # Startup script
├── register_employee.py         # Employee registration script
├── config.py                    # Settings (auto-created)
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

1. Check logs in `logs/system.log`
2. Confirm installed dependencies
3. Test camera separately
4. Check network connectivity

## License

This project is provided as-is, for educational and commercial use.

Developed using Python, OpenCV and Flask
