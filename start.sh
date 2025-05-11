#!/bin/bash

# Declare variables
TEMPLATE_DIR="./templates/"
BASE_PROJECT_DIR="./"

# Copy files
echo "Copying..."
for file in "$TEMPLATE_DIR"/*; do
    filename=$(basename "$file")
    
    # Check if the file already exists in the destination directory
    if [ -e "$BASE_PROJECT_DIR/$filename" ]; then
        echo "Skipping for $filename"
        continue
    fi
    
    cp "$file" "$BASE_PROJECT_DIR"
    echo "Copied $filename to $BASE_PROJECT_DIR"
done

if [[ ! -d ".venv" ]]; then
    echo ".venv not found in the current directory."
    read -p "Enter the path to your virtual environment or press ENTER to create a new one here: " VENV_PATH

    # Default to creating .venv in the current directory if no input
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
python3 flexidns.py
deactivate
exit
