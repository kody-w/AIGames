# Edge Deployment Guide - Offline AI Agent System

Complete guide for deploying Copilot Agent 365 on edge devices without internet connectivity. This configuration enables running AI agents entirely offline using local LLM models and local file storage.

## Overview

This system can now operate in **three deployment modes**:

1. **Cloud Mode** (Default): Azure OpenAI + Azure File Storage
2. **Hybrid Mode**: Azure OpenAI + Local File Storage
3. **Edge Mode** (Offline): Local LLM + Local File Storage ✅ **NEW**

## Edge Mode Architecture

```
┌─────────────────────────────────────────────────────┐
│              Edge Device (No Internet)              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐      ┌──────────────────────┐    │
│  │  Azure      │      │  Local LLM           │    │
│  │  Functions  │─────▶│  (Ollama/llama.cpp)  │    │
│  │  Runtime    │      │                      │    │
│  └─────────────┘      └──────────────────────┘    │
│         │                                          │
│         ▼                                          │
│  ┌─────────────┐      ┌──────────────────────┐    │
│  │  Agent      │      │  Local File Storage  │    │
│  │  System     │─────▶│  ~/.copilot-agent-   │    │
│  │             │      │  local/              │    │
│  └─────────────┘      └──────────────────────┘    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware Requirements (Minimum)

- **CPU**: 4 cores recommended (8+ for better performance)
- **RAM**: 8GB minimum (16GB+ recommended for larger models)
- **Storage**: 20GB free space (more for larger models)
- **OS**: Windows 10/11, macOS 11+, Linux (Ubuntu 20.04+)

### Software Requirements

1. **Python 3.11** (required for Azure Functions v4)
2. **Azure Functions Core Tools** v4
3. **Ollama** (for local LLM inference)

## Installation Steps

### 1. Install Python 3.11

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

**Linux (Ubuntu):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv
```

### 2. Install Azure Functions Core Tools

**macOS:**
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

**Windows:**
Download installer from [Microsoft Docs](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)

**Linux:**
```bash
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### 3. Install Ollama

**macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com/download/windows)

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 4. Download Local AI Model

Choose a model based on your hardware:

**Small models (8GB RAM):**
```bash
ollama pull llama2        # 7B parameters, ~4GB
ollama pull mistral       # 7B parameters, ~4GB
ollama pull phi           # 3B parameters, ~2GB
```

**Medium models (16GB RAM):**
```bash
ollama pull llama2:13b    # 13B parameters, ~8GB
ollama pull codellama     # 7B parameters, optimized for code
```

**Large models (32GB+ RAM):**
```bash
ollama pull llama2:70b    # 70B parameters, ~40GB
```

**Recommended for edge deployment:**
```bash
ollama pull llama2        # Best balance of performance and size
```

### 5. Configure Edge Deployment

The configuration is already set in `local.settings.json`:

```json
{
  "Values": {
    "USE_LOCAL_STORAGE": "true",
    "USE_LOCAL_LLM": "true",

    "LOCAL_LLM_BACKEND": "ollama",
    "LOCAL_LLM_MODEL": "llama2",
    "OLLAMA_ENDPOINT": "http://localhost:11434",
    "LOCAL_STORAGE_PATH": "",

    "AZURE_OPENAI_API_KEY": "",
    "AZURE_OPENAI_ENDPOINT": "",
    "AZURE_OPENAI_DEPLOYMENT_NAME": ""
  }
}
```

**Configuration Options:**

- `USE_LOCAL_STORAGE`: Set to "true" for local file storage
- `USE_LOCAL_LLM`: Set to "true" for local LLM (offline mode)
- `LOCAL_LLM_BACKEND`: "ollama" or "llamacpp"
- `LOCAL_LLM_MODEL`: Model name (e.g., "llama2", "mistral", "phi")
- `OLLAMA_ENDPOINT`: Ollama server endpoint
- `LOCAL_STORAGE_PATH`: Custom storage path (leave empty for default `~/.copilot-agent-local`)

### 6. Install Python Dependencies

```bash
cd Copilot-Agent-365-main
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Edge System

### 1. Start Ollama Server

**macOS/Linux:**
```bash
ollama serve
```

**Windows:**
Ollama runs as a Windows service automatically after installation.

**Verify Ollama is running:**
```bash
ollama list
```

### 2. Start Azure Functions Runtime

**macOS/Linux:**
```bash
cd Copilot-Agent-365-main
source .venv/bin/activate
func start --port 7071
```

**Windows:**
```powershell
cd Copilot-Agent-365-main
.\.venv\Scripts\activate
func start --port 7071
```

**Expected Output:**
```
🏠 Using LOCAL file storage (offline mode)
🤖 Using LOCAL LLM (offline mode)
📦 Model: llama2

Functions:

        businessinsightbot_function: [POST] http://localhost:7071/api/businessinsightbot_function
```

### 3. Test the System

**Test API endpoint:**
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello, are you running offline?",
    "conversation_history": []
  }'
```

**Expected Response:**
```json
{
  "assistant_response": "Yes, I am running completely offline...",
  "voice_response": "I'm running offline on your local device.",
  "agent_logs": "",
  "user_guid": "c0p110t0-aaaa-bbbb-cccc-123456789abc"
}
```

## Storage Locations

### Local File Storage

Default location: `~/.copilot-agent-local/`

**Directory Structure:**
```
~/.copilot-agent-local/
├── shared_memories/
│   └── memory.json              # Shared knowledge across all users
├── memory/
│   └── {user-guid}/
│       └── user_memory.json     # User-specific memories
├── agents/                       # Local agent files
├── multi_agents/                 # Multi-agent configurations
├── demos/                        # Demo scenarios
├── agent_config/                 # Agent configurations
├── logs/                         # Local logs
└── cache/                        # Local cache
```

**View storage statistics:**
```bash
ls -lh ~/.copilot-agent-local/
du -sh ~/.copilot-agent-local/
```

### Ollama Model Storage

**macOS:**
- Models: `~/.ollama/models/`
- Logs: `~/.ollama/logs/`

**Linux:**
- Models: `~/.ollama/models/`
- Logs: `/tmp/ollama.log`

**Windows:**
- Models: `C:\Users\<username>\.ollama\models\`
- Logs: `C:\Users\<username>\.ollama\logs\`

## Performance Tuning

### Optimize Ollama Performance

**Set CPU threads:**
```bash
export OLLAMA_NUM_THREADS=8  # Match your CPU cores
ollama serve
```

**Set GPU acceleration (if available):**
```bash
# NVIDIA GPU
export OLLAMA_CUDA_ENABLED=1

# AMD GPU
export OLLAMA_ROCM_ENABLED=1

# Apple Silicon (M1/M2/M3)
# Automatic - no configuration needed
```

### Adjust Model Context Window

Edit `local.settings.json`:
```json
{
  "Values": {
    "MAX_CONVERSATION_HISTORY": "10",  # Reduce for faster responses
    "OLLAMA_NUM_CTX": "2048"            # Context window size
  }
}
```

### Monitor Resource Usage

**macOS/Linux:**
```bash
# Monitor CPU/RAM
top
htop  # If installed

# Monitor Ollama
curl http://localhost:11434/api/tags
```

**Windows:**
```powershell
# Task Manager
taskmgr

# PowerShell monitoring
Get-Process ollama
```

## Troubleshooting

### Issue: "Local LLM initialization failed"

**Cause:** Ollama server not running

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Issue: "Model not found"

**Cause:** Model not downloaded

**Solution:**
```bash
# List available models
ollama list

# Download model
ollama pull llama2
```

### Issue: "Slow response times"

**Causes & Solutions:**

1. **CPU-only inference:** Use smaller model (phi, llama2:7b)
2. **Limited RAM:** Close other applications
3. **Large context window:** Reduce `MAX_CONVERSATION_HISTORY`

**Try lighter model:**
```bash
ollama pull phi  # Only 2GB
```

Update `local.settings.json`:
```json
{
  "Values": {
    "LOCAL_LLM_MODEL": "phi"
  }
}
```

### Issue: "Storage permission denied"

**Cause:** Cannot write to default storage location

**Solution:**
```bash
# Create custom storage directory
mkdir -p ~/my-copilot-storage
chmod 755 ~/my-copilot-storage
```

Update `local.settings.json`:
```json
{
  "Values": {
    "LOCAL_STORAGE_PATH": "/Users/yourname/my-copilot-storage"
  }
}
```

### Issue: "Function calling not working"

**Cause:** Smaller models may struggle with function calling

**Solution:**
Use a model with better instruction-following:
```bash
ollama pull mistral     # Better at function calling
ollama pull codellama   # Excellent for structured output
```

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/copilot-agent.service`:

```ini
[Unit]
Description=Copilot Agent 365 Edge Service
After=network.target ollama.service

[Service]
Type=simple
User=copilot
WorkingDirectory=/opt/copilot-agent-365
Environment="PATH=/opt/copilot-agent-365/.venv/bin"
ExecStart=/opt/copilot-agent-365/.venv/bin/func start --port 7071
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable copilot-agent
sudo systemctl start copilot-agent
sudo systemctl status copilot-agent
```

### Docker Deployment

Create `Dockerfile.edge`:

```dockerfile
FROM python:3.11-slim

# Install Azure Functions runtime
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && \
    mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg && \
    sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-debian-bullseye-prod bullseye main" > /etc/apt/sources.list.d/dotnetdev.list' && \
    apt-get update && \
    apt-get install -y azure-functions-core-tools-4

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy application
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Download model (at build time)
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama2

EXPOSE 7071 11434

CMD ["sh", "-c", "ollama serve & func start --port 7071"]
```

Build and run:
```bash
docker build -f Dockerfile.edge -t copilot-agent-edge .
docker run -p 7071:7071 -p 11434:11434 copilot-agent-edge
```

### Kubernetes Deployment

Create `edge-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: copilot-agent-edge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: copilot-agent-edge
  template:
    metadata:
      labels:
        app: copilot-agent-edge
    spec:
      containers:
      - name: copilot-agent
        image: copilot-agent-edge:latest
        ports:
        - containerPort: 7071
          name: http
        - containerPort: 11434
          name: ollama
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
          limits:
            memory: "16Gi"
            cpu: "8"
        env:
        - name: USE_LOCAL_STORAGE
          value: "true"
        - name: USE_LOCAL_LLM
          value: "true"
        - name: LOCAL_LLM_MODEL
          value: "llama2"
        volumeMounts:
        - name: storage
          mountPath: /root/.copilot-agent-local
        - name: ollama-models
          mountPath: /root/.ollama
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: copilot-storage-pvc
      - name: ollama-models
        persistentVolumeClaim:
          claimName: ollama-models-pvc
```

## Security Considerations

### Edge Device Hardening

1. **Firewall Configuration:**
```bash
# Only allow local connections
sudo ufw allow from 127.0.0.1 to any port 7071
sudo ufw allow from 127.0.0.1 to any port 11434
sudo ufw enable
```

2. **File Permissions:**
```bash
# Secure storage directory
chmod 700 ~/.copilot-agent-local
chmod 600 ~/.copilot-agent-local/memory/*/*.json
```

3. **Process Isolation:**
```bash
# Run as dedicated user
sudo useradd -r -s /bin/false copilot
sudo chown -R copilot:copilot /opt/copilot-agent-365
```

## Monitoring

### Health Check Endpoint

Check system status:
```bash
curl http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "status", "conversation_history": []}'
```

### Storage Monitoring

Check storage usage:
```bash
# Disk usage
du -sh ~/.copilot-agent-local

# File count
find ~/.copilot-agent-local -type f | wc -l

# Recent activity
ls -lt ~/.copilot-agent-local/memory/*/user_memory.json | head -5
```

### Performance Metrics

Monitor response times:
```bash
time curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Hello", "conversation_history": []}'
```

## Comparison: Cloud vs Edge

| Feature | Cloud Mode | Edge Mode |
|---------|-----------|-----------|
| **Internet Required** | Yes | No ✅ |
| **Latency** | 500-2000ms | 100-500ms ✅ |
| **Cost** | ~$0.01/1K tokens | Free ✅ |
| **Privacy** | Data sent to Azure | 100% local ✅ |
| **Model Quality** | GPT-4 (best) | Llama2/Mistral (good) |
| **Setup Complexity** | Medium | Higher |
| **Hardware Requirements** | None | 8GB+ RAM |
| **Scalability** | Unlimited | Limited by hardware |

## Use Cases

### Ideal Edge Deployments

1. **Military/Defense:** Air-gapped secure environments
2. **Industrial IoT:** Factory floors without internet
3. **Maritime:** Ships with limited connectivity
4. **Healthcare:** HIPAA-compliant offline processing
5. **Automotive:** In-vehicle AI assistants
6. **Remote Locations:** Oil rigs, research stations
7. **Privacy-Focused:** Financial institutions, legal firms

## Advanced Configuration

### Multiple LLM Backends

Switch between Ollama and llama.cpp:

**llama.cpp setup:**
```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Run server
./server -m models/llama-2-7b.gguf -c 2048
```

Update `local.settings.json`:
```json
{
  "Values": {
    "LOCAL_LLM_BACKEND": "llamacpp",
    "LLAMACPP_ENDPOINT": "http://localhost:8080"
  }
}
```

### Custom Model Fine-Tuning

Fine-tune a model for your domain:

```bash
# Export conversations
python utils/export_conversations.py > training_data.jsonl

# Fine-tune with Ollama
ollama create my-custom-model -f Modelfile

# Use custom model
```

Update `local.settings.json`:
```json
{
  "Values": {
    "LOCAL_LLM_MODEL": "my-custom-model"
  }
}
```

## Support

For issues specific to:
- **Azure Functions:** [Microsoft Docs](https://learn.microsoft.com/en-us/azure/azure-functions/)
- **Ollama:** [Ollama GitHub](https://github.com/ollama/ollama)
- **Copilot Agent 365:** [GitHub Issues](https://github.com/kody-w/Copilot-Agent-365/issues)

## Next Steps

1. ✅ System configured for edge deployment
2. 🔄 Test with local Ollama instance
3. 📊 Monitor performance and resource usage
4. 🔧 Optimize model selection for your hardware
5. 🚀 Deploy to production edge devices

---

**Version:** 1.0.0
**Last Updated:** 2025-01-07
**Status:** Production Ready
