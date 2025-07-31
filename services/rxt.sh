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

# copies missing resources from templates
if [ "$missing" = true ]; then
    echo "Failed some resources are missing..."
    echo "Please verify them and use 'systemctl restart udip.service' again."
    exit 1
fi

# parse args.txt
ARG_FILE="services/args.txt"
colon_vars=()
double_colon_vars=()
dash_vars=()

while IFS= read -r line; do
    # remove leading/trailing whitespace
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    if [[ "$line" == :* && "$line" != ::* ]]; then
        # remove ":"
        val="${line:1}"
        colon_vars+=($val)
    elif [[ "$line" == ::* ]]; then
        val="${line:2}"
        double_colon_vars+=("-$val")
    elif [[ "$line" == -* ]]; then
        dash_vars+=($line)
    fi
done < "$ARG_FILE"

# If module of virtual environment is already set.
ENV_NAME="${colon_vars[0]}"
ENV_PATH="${colon_vars[2]:-.$ENV_NAME}"

if [ -n "$ENV_NAME" ]; then
    if [[ ! -d "$ENV_PATH" ]]; then
        echo "Virtual environment not found at $ENV_PATH"
        echo "Creating a new virtual environment..."

        python3 -m "$ENV_NAME" "$ENV_PATH"
    fi

    source "$ENV_PATH/bin/activate"
    echo "Virtual environment activated at $ENV_PATH"
fi

# check if requirements.txt is satisfied
if ! pip3 freeze | grep -qF -f requirements.txt; then
    echo "Installing missing dependencies from requirements.txt..."
    pip3 install -r requirements.txt
fi

# build final command
CMD=(python3 "${double_colon_vars[@]}" main.py "${dash_vars[@]}")

echo "Starting the application..."
echo "> ${CMD[*]}"
"${CMD[@]}"

deactivate
exit
