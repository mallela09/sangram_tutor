#!/bin/bash
# Quick start script for Sangram Tutor

# Print colored messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}   Sangram Tutor - Quick Start Script   ${NC}"
echo -e "${YELLOW}=========================================${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.9 or newer.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

# Create directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data vector_indices

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install the package in development mode
echo -e "${YELLOW}Installing Sangram Tutor in development mode...${NC}"
pip install -e .
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install package in development mode.${NC}"
    exit 1
fi

# Install additional dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    # Continue anyway since we've already installed the package
    echo -e "${YELLOW}Continuing with installation from setup.py...${NC}"
fi

# Set PYTHONPATH to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo -e "${GREEN}PYTHONPATH set to: $PYTHONPATH${NC}"

# Run the application
echo -e "${GREEN}Starting Sangram Tutor API server...${NC}"
echo -e "${YELLOW}API will be available at: ${GREEN}http://localhost:8000${NC}"
echo -e "${YELLOW}API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run directly with Python to ensure proper module resolution
python -m main.py