Python 3.13.2 (v3.13.2:4f8bb3947cf, Feb  4 2025, 11:51:10) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> #!/bin/bash
... # run_tests.sh
... # Script to run the tests for Sangram Tutor
... 
... # Print colored messages
... GREEN='\033[0;32m'
... YELLOW='\033[1;33m'
... RED='\033[0;31m'
... NC='\033[0m' # No Color
... 
... echo -e "${YELLOW}=========================================${NC}"
... echo -e "${YELLOW}      Sangram Tutor - Test Runner       ${NC}"
... echo -e "${YELLOW}=========================================${NC}"
... 
... # Check if virtual environment exists
... if [ ! -d "venv" ]; then
...     echo -e "${RED}Virtual environment not found!${NC}"
...     echo -e "${YELLOW}Please run setup first:${NC}"
...     echo -e "${GREEN}./quick_start.sh${NC}"
...     exit 1
... fi
... 
... # Activate virtual environment
... echo -e "${YELLOW}Activating virtual environment...${NC}"
... source venv/bin/activate
... 
... # Set PYTHONPATH
... export PYTHONPATH=$PYTHONPATH:$(pwd)
... 
... # Run the tests
... echo -e "${YELLOW}Running tests...${NC}"
... pytest -xvs sangram_tutor/tests/
... 
