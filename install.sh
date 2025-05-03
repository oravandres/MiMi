#!/bin/bash

# Ask if git should be initialized
read -p "Initialize git repository? (y/n): " init_git

if [ "$init_git" == "y" ] || [ "$init_git" == "Y" ]; then
    echo "Initializing git repository..."
    
    # Initialize git repository
    git init
    
    # Create .gitignore
    cat > .gitignore << EOL
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
.idea/
.vscode/
*.swp
*~
.DS_Store
EOL
    
    # Add files
    git add .
    
    # Initial commit
    git commit -m "Initial commit of MiMi framework"
    
    echo "Git repository initialized!"
    echo "Don't forget to add a remote with:"
    echo "git remote add origin <repository-url>"
    echo ""
fi

echo "Setting up Python environment..."

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Ask if development dependencies should be installed
read -p "Install development dependencies? (y/n): " install_dev

if [ "$install_dev" == "y" ] || [ "$install_dev" == "Y" ]; then
    echo "Installing development dependencies..."
    pip install -r requirements-dev.txt
else
    echo "Installing core dependencies only..."
    pip install -r requirements.txt
fi

# Add the current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "export PYTHONPATH=\$PYTHONPATH:$(pwd)" >> venv/bin/activate

echo "MiMi installed successfully!"
echo "To use MiMi, activate the virtual environment with:"
echo "source venv/bin/activate" 