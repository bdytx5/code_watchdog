#!/bin/bash

# Exit immediately on error
set -e

echo "Starting the code_watchdog setup..."

# Step 1: Clone the repository
if [ ! -d "code_watchdog" ]; then
    echo "Cloning the code_watchdog repository from GitHub..."
    git clone https://github.com/bdytx5/code_watchdog.git
else
    echo "Repository already exists. Pulling the latest changes..."
    cd code_watchdog && git pull && cd ..
fi

cd code_watchdog

# Step 2: Create the Conda environment
if ! conda info --envs | grep -q "code_watchdog"; then
    echo "Creating Conda environment 'code_watchdog' with Python 3.10..."
    conda create --name code_watchdog python=3.10 -y
else
    echo "'code_watchdog' environment already exists."
fi

# Step 3: Activate the environment
echo "Activating the Conda environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate code_watchdog

# Step 4: Install required packages
echo "Installing required packages..."
conda install watchdog -y
pip install anthropic psutil weave

# Step 5: Set up ~/.cw directory and copy files
echo "Setting up the ~/.cw directory..."
mkdir -p ~/.cw
cp file_monitor.py ~/.cw/
cp fix.py ~/.cw/

# Step 6: Copy MOVE_THIS_sitecustomize.py to the correct location
SITE_CUSTOMIZE_PATH=$(conda info --base)/envs/code_watchdog/lib/python3.10/site-packages/
echo "Copying MOVE_THIS_sitecustomize.py to $SITE_CUSTOMIZE_PATH..."
mkdir -p "$SITE_CUSTOMIZE_PATH"
cp MOVE_THIS_sitecustomize.py "$SITE_CUSTOMIZE_PATH/sitecustomize.py"

# Step 7: Set up activation and deactivation scripts
ACTIVATE_DIR=$(conda info --base)/envs/code_watchdog/etc/conda/activate.d
DEACTIVATE_DIR=$(conda info --base)/envs/code_watchdog/etc/conda/deactivate.d

mkdir -p "$ACTIVATE_DIR" "$DEACTIVATE_DIR"

echo "Creating activation script..."
cat <<EOL > "$ACTIVATE_DIR/start_monitor.sh"
#!/bin/bash

# Start the file monitor in the background
nohup python ~/.cw/file_monitor.py > ~/.cw/monitor.log 2>&1 &
echo "Python file monitor started."
EOL

chmod +x "$ACTIVATE_DIR/start_monitor.sh"

echo "Creating deactivation script..."
cat <<EOL > "$DEACTIVATE_DIR/stop_monitor.sh"
#!/bin/bash

# Stop any running instances of file_monitor.py
pkill -f file_monitor.py
echo "Python file monitor stopped."
EOL

chmod +x "$DEACTIVATE_DIR/stop_monitor.sh"

# Step 8: Add alias for fix.py
echo "Adding alias 'cw' to ~/.bashrc or ~/.zshrc..."
if [ -f ~/.bashrc ]; then
    echo "alias cw='python ~/.cw/fix.py'" >> ~/.bashrc
    source ~/.bashrc
elif [ -f ~/.zshrc ]; then
    echo "alias cw='python ~/.cw/fix.py'" >> ~/.zshrc
    source ~/.zshrc
else
    echo "No .bashrc or .zshrc found. You may need to manually add the alias."
fi

# Step 9: Verify the setup
echo "Verifying setup... Activating and deactivating environment."

echo "Activating the environment..."
conda activate code_watchdog
echo "Deactivating the environment..."
conda deactivate

echo "Setup complete! Use 'conda activate code_watchdog' to start the monitor."
