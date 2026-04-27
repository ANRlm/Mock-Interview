import subprocess
from typing import Optional

class VRAMManager:
    def __init__(self):
        self._max_vram_mb = 16384  # 16GB budget for RTX 5080

    def get_vram_usage_mb(self) -> Optional[float]:
        """Query current VRAM usage via nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return float(result.stdout.strip().split('\n')[0])
        except Exception:
            pass
        return None

    def plan_allocation(self) -> dict:
        """Plan VRAM allocation across models."""
        return {
            "llm_qwen3_14b": 12288,  # ~12GB for qwen3:14b Q4
            "tts_qwen3_tts": 2048,   # ~2GB for Qwen3-TTS
            "stt_paraformer": 1024,  # ~1GB for Paraformer
            "buffer": 1024           # ~1GB buffer
        }

    def check_available(self, required_mb: int) -> bool:
        """Check if required VRAM is available."""
        current = self.get_vram_usage_mb()
        if current is None:
            return True  # Assume available if cannot query
        return (self._max_vram_mb - current) >= required_mb

vram_manager = VRAMManager()