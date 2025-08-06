# 🔥 Thermal Inspection System

A production-grade AI-powered thermal inspection system for electrical transmission infrastructure using FLIR thermal imaging and computer vision.

## 🚀 Features

- **Real-time Thermal Analysis**: Process FLIR thermal images with professional temperature mapping
- **AI Component Detection**: Automated detection of electrical components (nuts/bolts, joints, insulators, conductors)
- **IEEE C57.91 Compliance**: Professional defect classification following industry standards
- **Bulletproof Architecture**: Zero-crash guarantee with comprehensive error handling
- **REST API**: Complete FastAPI backend with interactive documentation
- **Health Monitoring**: Production-grade monitoring and logging system
- **Docker Deployment**: One-command production deployment

## 🏗️ Architecture

### Backend (FastAPI)
- **AI Pipeline**: YOLO-NAS + Pattern-based fallback detection
- **Thermal Engine**: FLIR data extraction and temperature analysis
- **Defect Classifier**: IEEE-compliant risk assessment
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **API**: RESTful endpoints with automatic documentation

### Frontend (React)
- **Dashboard**: Real-time monitoring interface
- **Upload System**: Drag-and-drop thermal image processing
- **Results Viewer**: Interactive analysis results and reports
- **Health Status**: System monitoring and diagnostics

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up --build
```

## 📡 API Endpoints

- **Main API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/api/docs`
- **Health Check**: `http://localhost:8000/api/health`
- **Upload**: `POST /api/upload`
- **Results**: `GET /api/analyses/{id}`

## 🔧 Configuration

Create a `.env` file:
```bash
DATABASE_URL=sqlite:///./thermal_inspection.db
ENVIRONMENT=development
UPLOAD_DIR=./static/thermal_images
PROCESSED_DIR=./static/processed_images
```

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest

# API testing
python test_api.py

# Database testing
python test_database.py
```

## 📊 Usage

1. **Start the system**:
   ```bash
   # Backend
   cd backend && python -m uvicorn app.main:app --reload
   
   # Frontend
   cd frontend && npm start
   ```

2. **Upload thermal images**: Navigate to `http://localhost:3000`

3. **View results**: Analysis results with temperature data and component detection

4. **Monitor health**: Check system status at `/api/health`

## 🛡️ Production Features

- **Zero-crash guarantee**: Comprehensive error handling
- **Failsafe AI**: Graceful degradation when models fail
- **File validation**: Security checks for uploaded images
- **Audit trails**: Complete processing history
- **Health monitoring**: Real-time system diagnostics

## 📁 Project Structure

```
thermal-inspection/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utilities
│   │   └── main.py         # Application entry point
│   ├── requirements.txt
│   └── Dockerfile.prod
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── services/       # API services
│   ├── package.json
│   └── public/
├── docker-compose.prod.yml # Production deployment
└── README.md
```

## 🔬 Technical Details

### AI Pipeline
- **Primary**: YOLO-NAS for component detection
- **Fallback**: Pattern-based detection using OpenCV
- **Thermal Processing**: FLIR EXIF extraction and Planck calibration

### Standards Compliance
- **IEEE C57.91**: Transformer loading guidelines
- **Temperature Thresholds**: Configurable ambient + rise limits
- **Risk Classification**: Critical/Potential/Normal zones

## 🚀 Deployment

### Development
```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Frontend  
cd frontend && npm start
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up --build
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions, please open an issue in the GitHub repository.

---

**Built for professional thermal inspection of electrical transmission infrastructure.** 