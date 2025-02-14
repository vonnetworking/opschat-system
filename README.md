# fm-opschat

# Setup
```bash
pip install -r src/agent/requirements.txt
```

# Usage

## CLI
```bash
python src/agent/lang_app_cli.py "Did any applications go down today?"
```

## FastAPI Backend
Run the backend server:
```bash
uvicorn src/backend/main:app --reload
```

  168  conda create --name opschat-py3.13 python=3.13
  169  conda activate opschat-py3.13
  170  history 


# Chat UI Setup
```bash
sudo apt install npm

cd chat-ui
npm install

npm install   
$ npm run dev -- --open
$ docker run -d -p 27017:27017 --name mongo-chatui mongo:latest
$ git clone https://github.com/huggingface/chat-ui
$ cd chat-ui
$ echo 'MONGODB_URL=mongodb://localhost:27017\nHF_TOKEN=your_hugging_face_access_token\nMODELS=[{"name":"microsoft/Phi-3-mini-4k-instruct","endpoints":[{"type":"llamacpp","baseURL":"http://localhost:8080"}]}]' > .env.local
$ brew install llama.cpp
$ llama-server --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf --hf-file Phi-3-mini-4k-instruct-q4.gguf -c 4096 &
```

## Running the Application

To start the server, simply run:
```
./start.sh
```

cd ~/fm-opschat/src
python -m server.main