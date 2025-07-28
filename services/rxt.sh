#!/bin/bash

# declare variables
BASE_PROJECT_DIR=$(pwd)
TEMPLATE_DIR="$BASE_PROJECT_DIR/templates/"

# verify resources
echo "Verifying resources..."
missing=false
for file in "$TEMPLATE_DIR"/*; do
    filename=$(basename "$file")

    if [ ! -e "$BASE_PROJECT_DIR/$filename" ]; then
        echo "Resource '$filename' is missing - copying..."
        cp "$file" "$BASE_PROJECT_DIR"
        missing=true
    fi
done

# copies miss resources from templates
if [ "$missing" = true ]; then
    echo "Failed some resources is missing..."
    echo "Please verify them and use 'systemctl restart flexidns.service' again."
    exit 1
fi

# using .venv environment
if [[ ! -d ".venv" ]]; then
    echo ".venv not found in the current directory."
    echo "Creating a new virtual environment in the current directory..."
    
    python3 -m venv .venv
    VENV_PATH=".venv"
else
    VENV_PATH=".venv"
fi

# activate the virtual environment
source "$VENV_PATH/bin/activate"
echo "Virtual environment activated at $VENV_PATH."

# check if requirements.txt is satisfied
if ! pip3 freeze | grep -qF -f requirements.txt; then
    echo "Installing missing dependencies from requirements.txt..."
    pip3 install -r requirements.txt
fi  

# run the application
echo "Starting the application..."
python3 flexidns.py $(grep -v '^#' services/args.txt)
deactivate

exit
