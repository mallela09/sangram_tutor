#!/bin/bash
# reset_environment.sh
# Script to reset the Sangram Tutor environment in case of issues

# Print colored messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}  Sangram Tutor - Environment Reset     ${NC}"
echo -e "${YELLOW}=========================================${NC}"

# Ask for confirmation
echo -e "${RED}WARNING: This will delete your virtual environment and any generated data.${NC}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${GREEN}Reset cancelled.${NC}"
    exit 0
fi

# Remove virtual environment
echo -e "${YELLOW}Removing virtual environment...${NC}"
if [ -d "venv" ]; then
    rm -rf venv
    echo -e "${GREEN}Virtual environment removed.${NC}"
else
    echo -e "${YELLOW}No virtual environment found.${NC}"
fi

# Remove generated data
echo -e "${YELLOW}Removing generated data...${NC}"
if [ -d "data" ]; then
    rm -rf data
    echo -e "${GREEN}Data directory removed.${NC}"
else
    echo -e "${YELLOW}No data directory found.${NC}"
fi

if [ -d "vector_indices" ]; then
    rm -rf vector_indices
    echo -e "${GREEN}Vector indices directory removed.${NC}"
else
    echo -e "${YELLOW}No vector indices directory found.${NC}"
fi

# Remove any cached Python files
echo -e "${YELLOW}Removing cached Python files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
echo -e "${GREEN}Cached Python files removed.${NC}"

# Clean up any egg-info directories
echo -e "${YELLOW}Removing egg-info directories...${NC}"
find . -type d -name "*.egg-info" -exec rm -rf {} +
echo -e "${GREEN}Egg-info directories removed.${NC}"

# Create fresh directories
echo -e "${YELLOW}Creating fresh directories...${NC}"
mkdir -p data vector_indices
echo -e "${GREEN}Fresh directories created.${NC}"

echo -e "${GREEN}Environment reset complete!${NC}"
echo -e "${YELLOW}To set up a fresh environment, run:${NC}"
echo -e "${GREEN}./quick_start.sh${NC}"
