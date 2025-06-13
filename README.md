# 🤖 ParManus with LLaVA 1.6

> **AI Agent Framework with Enhanced Browser Automation and LLaVA 1.6 Vision Model**
>
> Created by Parsu - An optimized AI agent framework featuring advanced browser automation, file handling, and multimodal capabilities using the LLaVA 1.6 model.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LLaVA 1.6](https://img.shields.io/badge/Model-LLaVA%201.6-green.svg)](https://llava-vl.github.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## ✨ Key Features

- **🌐 Advanced Browser Automation**: Navigate websites, search for content, and extract information
- **📁 Intelligent File Management**: Save search results, summaries, and content to organized files
- **🔍 Smart News Search**: Automatically fetch and summarize latest news from multiple sources
- **👁️ Vision Capabilities**: Process images and visual content using LLaVA 1.6 model
- **🧠 Multi-Agent Architecture**: Coordinated agents for different tasks (browser, file, chat)
- **⚡ Optimized Performance**: Efficient model loading, caching, and resource management
- **🛡️ Robust Error Handling**: Graceful fallbacks and recovery mechanisms

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- CUDA-capable GPU (recommended) or CPU
- 8GB+ RAM for optimal performance

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/parsu/parmanus.git
cd parmanus
```

2. **Create virtual environment:**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Download LLaVA 1.6 model:**
```bash
# Create models directory
mkdir models

# Download LLaVA 1.6 GGUF model (recommended)
# You can download from Hugging Face or use the provided script
python scripts/download_model.py
```

### Configuration

1. **Copy example config:**
```bash
cp config/config.example.toml config/config.toml
```

2. **Edit configuration:**
```toml
[llm]
model = "llava-1.6"
model_path = "./models/llava-v1.6.gguf"
vision_model_path = "./models/mmproj-model.gguf"
max_tokens = 2048
temperature = 0.7

[gpu]
force_cuda = true  # Set to false for CPU-only
enable_monitoring = true
```

### Running

```bash
python main.py
```

## 💡 Usage Examples

### News Search and Summarization
```
> Get the latest news today and save it as a file
```
The agent will:
1. Search for current news from multiple sources
2. Extract and summarize key information
3. Save results to `workspace/news_summary_YYYYMMDD_HHMMSS.txt`

### Web Content Extraction
```
> Go to https://example.com and summarize the main content
```

### File Operations
```
> Save this conversation to a file
```

### Image Analysis (LLaVA 1.6)
```
> Analyze this image and describe what you see
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Router Agent  │───▶│  Browser Agent  │───▶│   File Agent    │
│                 │    │                 │    │                 │
│ - Route tasks   │    │ - Web search    │    │ - Save content  │
│ - Coordination  │    │ - Navigation    │    │ - File ops      │
│ - Load balance  │    │ - Extraction    │    │ - Workspace     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │   LLaVA 1.6     │
                    │                 │
                    │ - Text + Vision │
                    │ - Tool calling  │
                    │ - Reasoning     │
                    └─────────────────┘
```

## 🛠️ Advanced Configuration

### GPU Optimization
```toml
[gpu]
force_cuda = true
gpu_layers = 27  # Adjust based on your GPU memory
enable_monitoring = true
memory_threshold = 0.8
```

### Browser Settings
```toml
[browser]
headless = true
timeout = 30
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### Model Settings
```toml
[llm]
context_length = 4096
batch_size = 512
threads = 8  # CPU threads for processing
```

## 📁 Project Structure

```
parmanus/
├── app/                    # Core application code
│   ├── agent/             # Agent implementations
│   ├── tool/              # Tool definitions
│   ├── prompt/            # Prompt templates
│   └── llm.py            # LLM interface
├── config/                # Configuration files
├── examples/              # Usage examples
├── scripts/               # Utility scripts
├── main.py               # Main entry point
└── requirements.txt      # Dependencies
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LLaVA Team** for the excellent multimodal model
- **Original Manus Project** for the foundational framework
- **Browser Use Library** for web automation capabilities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/parsu/parmanus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/parsu/parmanus/discussions)

---

**Created by Parsu** | Powered by LLaVA 1.6 🚀
