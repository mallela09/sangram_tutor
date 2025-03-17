# Sangram Tutor: AI-Powered Math Learning Platform

Sangram Tutor is an AI-powered educational application designed to help children learn mathematics in an engaging, personalized manner following the NCERT syllabus. This prototype demonstrates the core adaptive learning capabilities and personalization features.

## Project Overview

The prototype is focused on the backend functionality that powers the adaptive learning engine:

1. **Personalized Learning Paths**: AI-driven system that adapts to each student's learning style and progress
2. **Content Recommendation Engine**: Vector-based similarity and performance analysis for content recommendations
3. **Learning Style Detection**: Analysis of interaction patterns to identify preferred learning modalities
4. **Performance Analytics**: Comprehensive analysis of student performance with actionable insights
5. **RESTful API**: Complete API for client applications to interact with the learning platform

## System Requirements

- macOS 12+ (optimized for M1 MacBook)
- Python 3.9+
- 8GB+ RAM
- Docker (optional, for containerized deployment)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sangram-tutor.git
cd sangram-tutor
```

### 2. Quick Start (Recommended)

We provide a quick start script that handles all setup automatically:

```bash
# Make the script executable
chmod +x quick_start.sh

# Run the quick start script
./quick_start.sh
```

The script will:
1. Create a virtual environment
2. Install all dependencies
3. Set up the necessary directories
4. Install the package in development mode
5. Start the API server

### 3. Manual Setup

If you prefer to set up manually:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode
pip install -e .

# Create necessary directories
mkdir -p data vector_indices

# Set PYTHONPATH to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the API server
python -m sangram_tutor.main
```

### 4. Verify Installation

To verify that everything is installed correctly:

```bash
python verify_installation.py
```

### 5. Run the Demo (For Investors)

```bash
# Run the demonstration script
python demo/demo_script.py
```

This script showcases the core capabilities through a simulated student interaction.

## Troubleshooting

If you encounter any issues:

1. **ImportError or ModuleNotFoundError**:
   - Make sure you've installed the package in development mode with `pip install -e .`
   - Ensure your PYTHONPATH includes the root directory
   - Verify that all subpackages have `__init__.py` files

2. **Database Errors**:
   - Check if the `data` directory exists and is writable
   - Delete the database file and restart to recreate it

3. **Dependency Issues**:
   - Try installing dependencies separately: `pip install -r requirements.txt`
   - Ensure you're using Python 3.9+ with `python --version`

4. **Permission Issues**:
   - Make sure scripts are executable: `chmod +x quick_start.sh`

## Demo Features

The demonstration script illustrates:

1. **Adaptive Learning**: How the system adjusts content based on student performance
2. **Personalization**: Learning style detection and personalized recommendations
3. **Analytics**: Comprehensive performance analysis and insights
4. **Parent View**: Summary and recommendations for parents/guardians

## API Documentation

Once the server is running, API documentation is available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Core Architecture

### Data Models

- **User**: Student profiles with learning preferences and progress tracking
- **Curriculum**: NCERT-aligned topics and content with difficulty progression
- **Progress**: Detailed tracking of student interactions and achievements
- **Analytics**: Performance analysis and recommendation engines

### AI/ML Components

- **Learning Path Generator**: Creates personalized learning sequences
- **Content Recommender**: Suggests relevant learning material
- **Learning Style Detector**: Identifies preferred learning modalities
- **Performance Analyzer**: Provides insights on strengths and areas for improvement

## Development Roadmap

This prototype represents Phase 1 of the project. Future phases will include:

- Frontend application for students and parents
- Expanded curriculum coverage
- Enhanced AI capabilities using larger language models
- Multi-language support
- Advanced accessibility features

## Docker Deployment (Optional)

For a containerized deployment:

```bash
# Build and start containers
docker-compose up -d

# Access the API at http://localhost:8000
```

## Contact

For more information, please contact:
[Your Contact Information]

## License

[Appropriate License Information]
