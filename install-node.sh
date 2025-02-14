#!/bin/bash

# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Force load nvm immediately
export NVM_DIR="$HOME/.nvm"
source "$NVM_DIR/nvm.sh"
source "$NVM_DIR/bash_completion"

# Install and use Node.js 22
nvm install 22
nvm use 22
nvm alias default 22

# Verify installation
echo "Node.js version:"
node --version
echo "npm version:"
npm --version
