#!/bin/bash

TEMPLATE_DIR="./templates/"
BASE_PROJECT_DIR="./"

for file in "$TEMPLATE_DIR"/*; do
    filename=$(basename "$file")
    
    if [ -e "$BASE_PROJECT_DIR/$filename" ]; then
        continue
    fi
    
    cp "$file" "$BASE_PROJECT_DIR"
    echo "Copied $filename to $BASE_PROJECT_DIR"
done

if [[ ! -d ".venv" ]]; then
    echo ".venv not found in the current directory."
    read -p "Enter the path to your virtual environment or press ENTER to create a new one here: " VENV_PATH

    if [[ -z "$VENV_PATH" ]]; then
        echo "Creating a new virtual environment in the current directory..."
        python3 -m venv .venv
        VENV_PATH=".venv"
    fi
else
    VENV_PATH=".venv"
fi

# Activate the virtual environment
source "$VENV_PATH/bin/activate"
echo "Virtual environment activated at $VENV_PATH."

# Check if requirements.txt is satisfied
if ! pip3 freeze | grep -qF -f requirements.txt; then
    echo "Installing missing dependencies from requirements.txt..."
    pip3 install -r requirements.txt
fi  

# Run the application
echo "Starting the application..."
python3 udip.py
deactivate
exit
