#!/bin/bash
# Create project directory structure
mkdir -p sangram_tutor/{api,core,db,ml,models,utils,tests/{unit,integration}}
mkdir -p sangram_tutor/static/{content,images}

# Create initial files
touch sangram_tutor/__init__.py
touch sangram_tutor/api/__init__.py
touch sangram_tutor/core/__init__.py
touch sangram_tutor/db/__init__.py
touch sangram_tutor/ml/__init__.py
touch sangram_tutor/models/__init__.py
touch sangram_tutor/utils/__init__.py
touch sangram_tutor/tests/__init__.py
touch sangram_tutor/tests/unit/__init__.py
touch sangram_tutor/tests/integration/__init__.py

# Create project configuration files
echo "# Sangram Tutor - AI Math Learning Platform" > README.md

# Create Docker configuration
cat > Dockerfile << EOL
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "sangram_tutor.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOL

cat > docker-compose.yml << EOL
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=sqlite:///./sangram_tutor.db
      - SECRET_KEY=temporarysecretkeyfordevonly
    command: uvicorn sangram_tutor.main:app --host 0.0.0.0 --port 8000 --reload
EOL

# Create Python requirements file
cat > requirements.txt << EOL
fastapi==0.110.0
uvicorn==0.27.1
pydantic==2.6.1
sqlalchemy==2.0.25
alembic==1.13.1
python-jose==3.3.0
passlib==1.7.4
python-multipart==0.0.6
pytest==7.4.4
httpx==0.26.0
numpy==1.26.3
scikit-learn==1.4.0
faiss-cpu==1.7.4
tensorflow-macos==2.15.0
tensorflowjs==4.15.0
pandas==2.2.0
matplotlib==3.8.2
PyYAML==6.0.1
Jinja2==3.1.3
EOL

# Create Python virtual environment setup script
cat > setup_venv.sh << EOL
#!/bin/bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
EOL

chmod +x setup_venv.sh

echo "Project structure created successfully!"
