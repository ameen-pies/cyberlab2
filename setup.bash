#!/bin/bash

# Create main project directory
mkdir -p cybersec_platform
cd cybersec_platform

# Create directory structure
mkdir -p {api,streamlit_app,shared,tests}
mkdir -p api/{routes,models,services,middleware,utils}
mkdir -p streamlit_app/{pages,components,utils}
mkdir -p shared/{schemas,config}

# Create __init__.py files
touch api/__init__.py
touch api/routes/__init__.py
touch api/models/__init__.py
touch api/services/__init__.py
touch api/middleware/__init__.py
touch api/utils/__init__.py
touch streamlit_app/__init__.py
touch streamlit_app/pages/__init__.py
touch streamlit_app/components/__init__.py
touch streamlit_app/utils/__init__.py
touch shared/__init__.py
touch shared/schemas/__init__.py
touch shared/config/__init__.py
touch tests/__init__.py

# Create main files
touch api/main.py
touch streamlit_app/app.py
touch shared/config/settings.py
touch shared/schemas/user.py
touch shared/schemas/mfa.py
touch api/models/user.py
touch api/services/auth_service.py
touch api/services/email_service.py
touch api/services/encryption_service.py
touch api/routes/auth.py
touch api/routes/simulations.py
touch api/middleware/auth_middleware.py
touch api/utils/crypto.py
touch streamlit_app/pages/login.py
touch streamlit_app/pages/register.py
touch streamlit_app/pages/dashboard.py
touch streamlit_app/pages/encryption_sim.py
touch streamlit_app/components/sidebar.py
touch streamlit_app/utils/api_client.py
touch requirements.txt
touch .env.example
touch .gitignore
touch README.md

echo "✅ Project structure created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. cp .env.example .env"
echo "2. Edit .env with your MongoDB URI and SMTP credentials"
echo "3. pip install -r requirements.txt"
echo "4. python api/main.py (in one terminal)"
echo "5. streamlit run streamlit_app/app.py (in another terminal)"
echo ""
echo "📁 Directory tree:"
tree -I '__pycache__|*.pyc' || find . -type f -name "*.py" -o -name "*.txt" -o -name ".*" | grep -v __pycache__