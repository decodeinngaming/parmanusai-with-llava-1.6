# ParManus Local Model Configuration

This document explains the local model configuration implemented in the Dockerfile and docker-compose.yml.

## Overview

The configuration has been updated to use specific GGUF models without requiring API keys:

1. The Dockerfile downloads the specific models directly from HuggingFace
2. Models are stored in a persistent volume for caching
3. The Docker Compose file sets up a named volume for persistent model storage
4. Models are downloaded once and cached for future container runs

## Models

The following models are currently used:

1. **LLaVA-1.6-Mistral-7B**: A multimodal LLaMA model for both text and vision capabilities
   - Format: GGUF (Quantized)
   - Stored as: `/models/llava-v1.6.gguf`
   - Used for: Text generation and vision tasks

2. **MMProj Model**: Multimodal projection model used with LLaVA
   - Format: GGUF
   - Stored as: `/models/mmproj-model.gguf`
   - Used for: Vision feature extraction

## Usage

To use the configured models:

```bash
# Run with preconfigured model paths in config.toml
python main_optimized.py
```

The system will automatically detect and use the models specified in your configuration file.

## Configuration Details

- Models are stored locally at paths defined in config.toml:
  - `/models/llava-v1.6.gguf` - Main LLM model for text and vision
  - `/models/mmproj-model.gguf` - Multimodal projection model

- GPU Optimization Features:
  - CUDA support with automatic detection
  - Adjustable GPU layer allocation based on available memory
  - Memory monitoring and automatic cleanup at configurable thresholds
  - Fallback to CPU when necessary

- Performance Configuration:
  - Context sizes: 8192 for text, 2048 for vision
  - Thread allocation: 8 for text, 4 for vision
  - Quality preservation settings with fallback strategies

- No API keys are required for model usage
