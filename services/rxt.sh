#!/bin/bash

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

# Colon variables arguments name
VAR_NAME="${colon_vars[0]}"

# If module of virtual environment is already set.
ENV_NAME="${colon_vars[1]}"
ENV_PATH="${colon_vars[2]:-.$ENV_NAME}"
ENV_PYVER="${colon_vars[3]}"
if [[ "$VAR_NAME" == "module" ]]; then
    if [[ "$ENV_NAME" == "venv" ]]; then
        echo "Virtual environment not found at $ENV_PATH"
        echo "Creating a new virtual environment..."
        python3 -m "$ENV_NAME" "$ENV_PATH"

        echo "Activating virtual environment..."
        source "$ENV_PATH/bin/activate"
    elif [[ "$ENV_NAME" == "conda" ]]; then
        echo "Virtual environment not found at $ENV_PATH"
        echo "Creating a new virtual environment..."
        conda create -p "$ENV_NAME" $ENV_PYVER -y

        echo "Activating virtual environment..."
        conda activate "$ENV_PATH"
    else
        echo "Unsupported virtual environment type: $ENV_NAME"
        exit 1
    fi
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
