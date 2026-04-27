from __future__ import annotations

import torch
from pathlib import Path


def _init_gpu_settings() -> None:
    if torch.cuda.is_available():
        # CuDNN optimizations
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True
        
        # High precision matmul
        if hasattr(torch, "set_float32_matmul_precision"):
            torch.set_float32_matmul_precision("high")
        
        # Memory format optimization for inference
        torch.backends.cudnn.allow_tf32 = True
        
        # Flash Attention if available
        if hasattr(torch.nn.functional, 'scaled_dot_product_attention'):
            torch.backends.cuda.enable_flash_sdp(True)
        
        # Enable math SDP
        torch.backends.cuda.enable_math_sdp(True)
        
        # Memory pool optimization
        if hasattr(torch.cuda, 'set_per_process_memory_fraction'):
            # Reserve 10% for system
            torch.cuda.set_per_process_memory_fraction(0.9)
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {props.name} ({props.total_memory / 1024**3:.1f}GB)")
        print(f"CUDA version: {torch.version.cuda}")
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
    else:
        print("No CUDA GPU available, using CPU")


_init_gpu_settings()

from app.config import settings
from app.services.rag_service import rag_service
from app.services.stt_service import stt_service
from app.services.tts_service import tts_service
from app.services.tts_text_service import tts_text_normalizer


async def run_startup_tasks() -> None:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_DB_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TTS_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    tts_text_normalizer.force_reload()
    await stt_service.ensure_model_ready()
    await tts_service.ensure_ready()
    await rag_service.ensure_indexes()
