# Sangram Tutor Backend Architecture

## Overview

The backend for Sangram Tutor is designed as a modular Python-based system optimized to run locally on an M1 MacBook. It prioritizes the core AI/ML functionalities required for personalized learning while maintaining a lightweight footprint.

## Core Components

### 1. Data Models
- Student profiles and learning progress
- Curriculum mapping to NCERT standards
- Content repository (questions, explanations, exercises)
- Learning pathways and progression rules

### 2. AI/ML Services
- Adaptive learning algorithm
- Student performance assessment
- Content recommendation engine
- Learning style classification

### 3. API Layer
- RESTful endpoints for client applications
- GraphQL interface for flexible querying
- Authentication and authorization
- Data validation and sanitization

### 4. Persistence Layer
- Local database with schema migration
- In-memory caching for performance
- Vector storage for concept relationships
- File storage for educational content

### 5. Service Orchestration
- Asynchronous task processing
- Event-driven architecture for system components
- Logging and monitoring
- Configuration management

## Technical Stack

### Core Technologies
- **Language**: Python 3.12
- **Web Framework**: FastAPI
- **Database**: SQLite for development (PostgreSQL-compatible)
- **ORM**: SQLAlchemy 2.0
- **AI/ML**: scikit-learn, TensorFlow Lite, PyTorch
- **Vector DB**: FAISS (Facebook AI Similarity Search) for local embedding storage
- **Cache**: Simple in-memory cache with TTL

### Supporting Libraries
- **API Documentation**: Swagger/OpenAPI
- **Data Validation**: Pydantic v2
- **Authentication**: JWT tokens
- **Testing**: pytest
- **Type Checking**: mypy
- **Code Formatting**: black, isort

## Development Setup

The entire system will be containerized using Docker to ensure consistency regardless of the host environment. For an M1 MacBook, we'll use ARM64 compatible images.

## System Requirements (M1 MacBook)
- macOS Monterey or newer
- 8GB+ RAM
- 20GB available disk space
- Docker Desktop for Apple Silicon
- Python 3.10+ (for development outside container)

## Prototype Scope

For the initial prototype, we'll focus on:

1. **Core Data Models**
   - Student profile with learning preferences
   - Grade 1-3 math curriculum modules
   - Question and exercise database
   - Learning progress tracking

2. **Basic AI Functionality**
   - Difficulty adaptation algorithm
   - Performance prediction model
   - Content sequencing logic
   - Simple recommendation engine

3. **Essential APIs**
   - Student management
   - Content retrieval
   - Progress tracking
   - Basic analytics

4. **Demo Scripts**
   - Simulated student learning flows
   - Performance visualization
   - Algorithm effectiveness demonstration
   - A/B testing capabilities

This architecture balances sophistication with rapid development, enabling us to demonstrate the core value proposition to investors while establishing a foundation for future expansion.
