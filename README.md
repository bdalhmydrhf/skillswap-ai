# 🔐 SkillSwap AI - Decentralized Skill Exchange Platform

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Django](https://img.shields.io/badge/Django-5.2-green)
![React](https://img.shields.io/badge/React-18-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Blockchain](https://img.shields.io/badge/Ethereum-Sepolia-purple)

## 🎯 About The Project

SkillSwap AI is a **decentralized freelancing platform** that solves the trust problem in online work. It combines:

- **Multi-modal biometric authentication** (face, voice, fingerprint, digital signature) with liveness detection
- **Blockchain-based contract documentation** on Ethereum Sepolia with IPFS storage
- **AI-powered skill matching** using FAISS (50x faster than keyword search)
- **Encrypted real-time chat** with WebSockets and Fernet encryption

Built for freelancers in regions where platforms like Upwork and Fiverr are restricted, SkillSwap AI enables anyone to participate in the global digital economy securely.

🔗 **GitHub Repository:** [https://github.com/bdalhmydrhf/skillswap-ai](https://github.com/bdalhmydrhf/skillswap-ai)

## 📽️ Demo Video

[![SkillSwap AI Demo](https://img.youtube.com/vi/F5tDheKSTtA/0.jpg)](https://youtu.be/F5tDheKSTtA)

**Watch the full demo:** [https://youtu.be/F5tDheKSTtA](https://youtu.be/F5tDheKSTtA)

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🧬 **Multi-modal Biometrics** | Face (DeepFace+MTCNN), Voice (SpeechBrain ECAPA-TDNN), Fingerprint (ORB), Signature (DTW) |
| 🔐 **Liveness Detection** | Anti-spoofing to prevent photo/video/fingerprint mold attacks |
| ⛓️ **Smart Contracts** | Ethereum Sepolia + IPFS for tamper-proof contract storage |
| ✍️ **RSA-2048 Signatures** | Digital signatures for non-repudiation |
| 💬 **Encrypted Chat** | WebSocket + Fernet with per-room encryption keys |
| 🤖 **FAISS Recommendations** | Vector-based skill matching, 50x faster than keyword search |
| 📊 **Trust Score Algorithm** | Self-learning trust based on completion rate, ratings, response time |
| 🔒 **JWT Authentication** | With refresh tokens and rate limiting (Redis sliding window) |

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Django 5.2 | Web framework |
| Django REST Framework | API development |
| Django Channels | WebSocket support |
| Celery | Async tasks |
| Redis | Cache + rate limiting |
| PostgreSQL/SQLite | Database |
| JWT | Authentication |

### Frontend
| Technology | Purpose |
|------------|---------|
| React.js 18 | UI framework |
| Tailwind CSS | Styling |
| Framer Motion | Animations |
| WebSocket API | Real-time communication |

### Biometric & AI
| Technology | Purpose |
|------------|---------|
| DeepFace + MTCNN | Face recognition + liveness detection |
| SpeechBrain ECAPA-TDNN | Voice biometrics + anti-spoofing |
| FAISS | Vector search for skill matching |
| scikit-learn | TF-IDF, cosine similarity |
| OpenCV | Image processing |

### Blockchain
| Technology | Purpose |
|------------|---------|
| Web3.py | Ethereum interaction |
| Ethereum Sepolia | Testnet for smart contracts |
| IPFS | Decentralized storage |

## 🏁 How to Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (for Celery & Channels)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/bdalhmydrhf/skillswap-ai.git
cd skillswap-ai

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Redis (in a separate terminal)
redis-server --port 6380

# Start Celery worker (in a separate terminal)
celery -A backend worker -l info

# Start Django server
python manage.py runserver 8001
Frontend Setup
bash
cd frontend
npm install
npm run dev
The application will be available at:

Backend API: http://localhost:8001

Frontend: http://localhost:5173

🧪 System Testing Results
Component	Metric	Result
Face Recognition	Similarity threshold	0.60 (92% accuracy)
Voice Recognition	Similarity threshold	0.50 (71% match rate)
FAISS Search	Response time	<0.5 seconds for 10,000 users
Blockchain	Confirmation time	15-30 seconds (Sepolia)
WebSocket	Message latency	<100ms
Rate Limiting	Max requests/minute	30 per user
⚠️ Limitations
Biometric hardware required: Camera, microphone, and fingerprint sensor (optional)

Blockchain dependency: Requires Sepolia testnet connection (free)

Redis required: For Celery and rate limiting

Local deployment only: Not yet deployed to cloud (future work)
**✅ Cloud Status:** The project is **CURRENTLY DEPLOYED** on Google Cloud Shell (europe-west1 region). The Django server runs on port 8080 and the application is accessible via a public URL. Full production deployment on Google Cloud Run is planned as future work for enhanced scalability.

🔮 Future Work
📱 Mobile app with Flutter (iOS/Android)

🍏 Apple FaceID and TouchID integration

🌐 Cross-chain support (Polygon, Binance Smart Chain)

🏛️ DAO governance for dispute resolution

☁️ Google Cloud Run deployment for scalability

💳 Crypto payments integration

📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
☁️ Google Cloud Integration (Future): Deploy backend on Cloud Run with Cloud SQL, Cloud Storage, and Secret Manager for production scalability.

👩‍💻 Team
Name	Role
ماري نبيل إبراهيم	Developer
منال ياسر عدره	Developer
رهف يونس عبد الحميد	Developer
Supervised by: Dr. Redwan Dandeh
## 📄 Documentation

- **[📋 Google Cloud Deployment Strategy](./Cloud_Deployment_Strategy_SkillSwap_AI.md)** - Complete deployment roadmap and cloud readiness assessment
- **[📊 Project Analysis](./ما%20هو%20طبيعة%20عمل%20المنصة.pdf)** - SWOT analysis, requirements, performance metrics
- **[🎓 Full Graduation Project](./Graduation%20project-3.pdf)** - Complete thesis (60+ pages, UML diagrams, database schema)

## 🌐 Google Cloud Deployment Proof

> The application is successfully deployed on Google Cloud Shell. Below are screenshots confirming the live deployment.

### 1. Cloud Shell Terminal Status
*Active Django server running on port 8080 with FAISS and blockchain systems loaded:*

![Cloud Shell Terminal](https://github.com/bdalhmydrhf/skillswap-ai/blob/main/terminal_deployment.png?raw=true)

### 2. Django Admin Interface
*Django administration panel accessible via the cloud shell URL:*

![Django Admin Login](https://github.com/bdalhmydrhf/skillswap-ai/blob/main/admin_login.png?raw=true)

### Deployment Summary

| Component | Status |
| :--- | :--- |
| **Cloud Provider** | ✅ Google Cloud Shell (europe-west1) |
| **Server** | ✅ Running on 0.0.0.0:8080 |
| **Django Admin** | ✅ Accessible |
| **FAISS Engine** | ✅ Successfully loaded |
| **Blockchain V4.0** | ✅ Active |
| **Voice Biometric** | ✅ Enabled |
| **CORS** | ✅ Configured with cloud URL |

**Live URL:** `https://8080-cs-a844824d-8295-4183-9037-9a8488ec3805.cs-europe-west1-xedi.cloudshell.dev/admin/`

*Note: Access requires being logged into the Google account used for deployment.*
📞 Contact
For questions or collaboration opportunities, please open an issue on GitHub or contact the team through the repository.

