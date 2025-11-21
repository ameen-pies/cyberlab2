<<<<<<< HEAD
# 🔐 CyberSec Platform

Enterprise-grade cybersecurity simulation platform with MFA authentication and encryption demonstrations.

## Features

- ✅ Multi-Factor Authentication (Email-based)
- ✅ Argon2 Password Hashing
- ✅ JWT Token Authentication
- ✅ Encryption In Transit Simulation (TLS/SSL)
- ✅ Encryption At Rest Simulation (Database/Storage)
- ✅ MongoDB Atlas Integration
- ✅ FastAPI Backend
- ✅ Streamlit Frontend

## Tech Stack

- **Backend**: FastAPI, Motor (async MongoDB)
- **Frontend**: Streamlit
- **Database**: MongoDB Atlas
- **Authentication**: JWT, Argon2, Email MFA
- **Encryption**: Cryptography (Fernet, PBKDF2)

## Setup Instructions

### 1. Create Project Structure

```bash
chmod +x setup.sh
./setup.sh
```

Or manually run the commands from the setup script.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required configurations:
- MongoDB Atlas connection string
- SMTP credentials (Gmail recommended)
- Secret key for JWT

**Gmail SMTP Setup:**
1. Enable 2FA on your Google account
2. Generate an App Password: Google Account → Security → 2-Step Verification → App passwords
3. Use the generated password in `SMTP_PASSWORD`

### 4. Run the API

```bash
cd api
python main.py
```

Or with uvicorn:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 5. Run the Streamlit App

In a new terminal:

```bash
streamlit run streamlit_app/app.py
```

App will be available at: `http://localhost:8501`

## Usage

### Register & Login
1. Open the Streamlit app
2. Register a new account
3. Login with your credentials
4. Check your email for the MFA code
5. Enter the MFA code to complete authentication

### Encryption Simulations

**In Transit (TLS/SSL):**
- Simulates data encryption during network transmission
- Uses password-derived keys with PBKDF2
- AES-256 encryption via Fernet

**At Rest (Storage):**
- Simulates database/file encryption
- Uses randomly generated keys
- Demonstrates secure key storage concepts

**Full Lifecycle:**
- Complete end-to-end encryption demo
- Shows data flow: storage → retrieval → transmission

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (requires MFA)
- `POST /auth/mfa/send` - Send MFA code
- `POST /auth/mfa/verify` - Verify MFA & get JWT

### Simulations (Protected)
- `POST /simulations/encrypt/in-transit` - Encrypt for transit
- `POST /simulations/decrypt/in-transit` - Decrypt transit data
- `POST /simulations/encrypt/at-rest` - Encrypt for storage
- `POST /simulations/decrypt/at-rest` - Decrypt stored data
- `POST /simulations/encrypt/lifecycle` - Full demo

## Project Structure

```
cybersec_platform/
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   ├── auth.py            # Auth endpoints
│   │   └── simulations.py     # Simulation endpoints
│   ├── services/
│   │   ├── auth_service.py    # Auth logic
│   │   ├── email_service.py   # Email sending
│   │   └── encryption_service.py  # Encryption demos
│   ├── models/
│   │   └── user.py            # User model
│   ├── middleware/
│   │   └── auth_middleware.py # JWT verification
│   └── utils/
│       └── crypto.py          # Crypto utilities
├── streamlit_app/
│   ├── app.py                 # Main Streamlit app
│   └── utils/
│       └── api_client.py      # API wrapper
├── shared/
│   ├── config/
│   │   └── settings.py        # Config management
│   └── schemas/
│       ├── user.py            # User schemas
│       └── mfa.py             # MFA schemas
├── requirements.txt
├── .env.example
└── README.md
```

## Security Features

- **Argon2**: Memory-hard password hashing (no bcrypt!)
- **JWT**: Secure token-based authentication
- **MFA**: Time-limited email codes
- **AES-256**: Industry-standard encryption
- **PBKDF2**: Key derivation with high iteration count
- **MongoDB**: Secure cloud database with encryption at rest

## Development

### Add New Simulations

1. Create service in `api/services/`
2. Add routes in `api/routes/simulations.py`
3. Create UI in `streamlit_app/app.py`
4. Update API client in `streamlit_app/utils/api_client.py`

## Troubleshooting

**MongoDB Connection Issues:**
- Verify connection string in `.env`
- Whitelist your IP in MongoDB Atlas
- Check network connectivity

**Email Not Sending:**
- Verify SMTP credentials
- Use App Password for Gmail
- Check firewall/antivirus settings

**Import Errors:**
- Ensure all `__init__.py` files exist
- Run from project root directory
- Check Python path

## License

MIT

=======
