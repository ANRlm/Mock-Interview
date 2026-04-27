# GPU Acceleration Optimization Plan

## Current State
- **GPU**: NVIDIA GeForce RTX 5080 Laptop (16GB VRAM) - only 1% utilized
- **Services with GPU**: CosyVoice2 (TTS), Ollama (LLM)
- **Services WITHOUT GPU**: FunASR (STT), Backend API, Embeddings, ChromaDB

## Optimization Targets

### 1. FunASR (STT) - Enable GPU Acceleration
- Currently missing GPU configuration
- Add `gpus: all` and CUDA environment variables
- Use `nvidia/cuda:12.6.0-cudnn-runtime-ubuntu22.04` base image

### 2. Backend API - Add GPU-accelerated Services
- Enable PyTorch CUDA for embedding calculations
- Add GPU-accelerated vector operations
- Configure `torch.backends.cudnn.benchmark = true`
- Enable `torch.compile()` where applicable

### 3. Embedding Service - GPU Acceleration
- BAAI/bge-m3 embedding model should run on GPU
- Add batch processing for embeddings
- Configure proper CUDA device allocation

### 4. ChromaDB - GPU Acceleration (if supported)
- Configure Chroma to use GPU for vector search
- Add GPU memory management

### 5. Vision Analysis Service - GPU Acceleration
- Eye contact, facial expression analysis currently CPU-only
- Add GPU acceleration for these models

### 6. Docker Compose Optimizations
- Add `deploy.resources.reservations` for GPU memory
- Configure `NVIDIA_VISIBLE_DEVICES` consistently
- Add `NVIDIA_DRIVER_CAPABILITIES: compute,utility,video`

### 7. Backend PyTorch Optimizations
- Enable `torch.backends.cudnn.benchmark`
- Set `torch.set_float32_matmul_precision('high')`
- Configure proper batch sizes for GPU
- Add model warmup on startup

## Implementation Order
1. Update docker-compose.gpu.yml for FunASR GPU support
2. Add PyTorch CUDA configuration to backend
3. Create GPU-accelerated embedding service wrapper
4. Add GPU optimizations to vision service
5. Add backend GPU initialization on startup
6. Verify all services with nvidia-smi