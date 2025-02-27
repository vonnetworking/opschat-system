# FM Ops Chat

## Project Overview
A basic operations chat application integrating a Flask-based back-end with a web-based Chat UI.





## How to run:

```bash
# Build the application containers
./opschat.sh build # add --new if need to build without any caching

# Run the application
./opschat.sh run

```
### Accessing the Application

After running `./opschat.sh run`, you'll see output similar to:

```bash
🔹 Container name: ye-opschat-4531
🔹 FastAPI: http://10.128.135.97:41937 or http://localhost:41937
🔹 Chat UI: http://10.128.135.97:50137 or http://localhost:50137
```

-------- OBSOLETE TO CLEAN UP LATER ON-----
## Requirements

- Python 3.13
- Node 22

# Setup
```bash
./install-node.sh
pip install -r src/requirements.txt
```

## Usage

### CLI
```bash
# Create and activate a Python 3.13 environment
conda create --name opschat-py3.13 python=3.13
conda activate opschat-py3.13
```


## Running the Application

To start the server, simply run:
```bash
./start.sh
```

# This section is for dev only and subject to change (do it and be careful)

## Chat UI Setup
Ensure Node.js and npm are installed, then run:
```bash
sudo apt install npm
cd chat-ui
npm install
npm run dev -- --open
```

To run MongoDB for Chat UI:
```bash
docker run -d -p 27017:27017 --name mongo-chatui mongo:latest
```

Clone the Chat UI repository and prepare environment variables: (alredy done)
```bash
git clone https://github.com/huggingface/chat-ui
cd chat-ui
echo 'MONGODB_URL=mongodb://localhost:27017
HF_TOKEN=your_hugging_face_access_token
MODELS=[{"name":"microsoft/Phi-3-mini-4k-instruct","endpoints":[{"type":"llamacpp","baseURL":"http://localhost:8080"}]}]' > .env.local
```

Install llama.cpp and start the llama server:
```bash
brew install llama.cpp
llama-server --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf --hf-file Phi-3-mini-4k-instruct-q4.gguf -c 4096 &
```


or using the Python module:
```bash
cd ~/fm-opschat/src
python -m server.main
```

# OpsChatUI

## Networking Guide

OpsChatUI uses Docker networking to connect multiple services:

### Access from Your Browser
- **Chat UI**: http://localhost:5173 (or dynamically assigned port)
- **FastAPI Backend**: http://localhost:1234 (or dynamically assigned port)

### Inter-Container Communication
Services inside Docker communicate using container names:
- MongoDB: `mongo-chatui:27017`
- Qdrant: `romantic_solomon:6333`
- Ollama: `ollama:11434`
- FastAPI (from ChatUI): `localhost:1234` (as they share the same container)

### Configuration Files
Key files that handle networking:
- `opschat.sh`: Creates Docker network, connects containers, publishes ports
- `docker-entrypoint.sh`: Sets environment variables for services  
- `chat-ui/.env.local`: Configures MongoDB and API connections

### Run the Application
```bash
./opschat.sh all   # Build and run
./opschat.sh run   # Run only
```

Check the displayed URLs once the application starts.