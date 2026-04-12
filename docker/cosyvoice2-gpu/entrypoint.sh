#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${HF_HOME:-/models/huggingface}" "${MODELSCOPE_CACHE:-/models/modelscope}" "${TORCH_HOME:-/models/torch}"

MODEL_DIR="${COSYVOICE_MODEL_DIR:-iic/CosyVoice2-0.5B}"
CPU_POLICY="$(printf '%s' "${COSYVOICE_FORCE_CPU:-auto}" | tr '[:upper:]' '[:lower:]')"
FORCE_CPU=0

if [ "$CPU_POLICY" = "1" ] || [ "$CPU_POLICY" = "true" ] || [ "$CPU_POLICY" = "yes" ]; then
  FORCE_CPU=1
elif [ "$CPU_POLICY" = "auto" ]; then
  set +e
  python3 - <<'PY'
import sys

try:
    import torch
except Exception:
    sys.exit(0)

if not torch.cuda.is_available():
    sys.exit(0)

try:
    major, minor = torch.cuda.get_device_capability(0)
    expected_arch = f"sm_{major}{minor}"
    available_arches = set(torch.cuda.get_arch_list() or [])
except Exception:
    sys.exit(0)

if expected_arch not in available_arches:
    print(
        f"CUDA arch {expected_arch} not in torch support list {sorted(available_arches)}; falling back to CPU",
        flush=True,
    )
    sys.exit(42)

sys.exit(0)
PY
  probe_status=$?
  set -e
  if [ "$probe_status" -eq 42 ]; then
    FORCE_CPU=1
  fi
fi

if [ "$FORCE_CPU" -eq 1 ]; then
  export CUDA_VISIBLE_DEVICES=""
  echo "CosyVoice runtime using CPU path"
else
  echo "CosyVoice runtime using CUDA path"
fi

cd /opt/CosyVoice

python3 - <<'PY'
import gc
import os
import subprocess
import sys
from pathlib import Path

repo_dir = Path.cwd()
sys.path.append(str(repo_dir / "third_party/Matcha-TTS"))

from cosyvoice.cli.cosyvoice import AutoModel

spk_id = os.getenv("COSYVOICE_VOICE", "default_zh")
prompt_wav = os.getenv("COSYVOICE_PROMPT_WAV", str(repo_dir / "asset/zero_shot_prompt.wav"))
if not os.path.isabs(prompt_wav):
    prompt_wav = str((repo_dir / prompt_wav).resolve())

pitch_semitones = float(os.getenv("COSYVOICE_PROMPT_PITCH_SEMITONES", "0") or 0)
tempo = float(os.getenv("COSYVOICE_PROMPT_TEMPO", "1.0") or 1.0)
if abs(pitch_semitones) > 0.01 or abs(tempo - 1.0) > 0.01:
    adjusted_prompt = Path("/tmp/cosyvoice_prompt_adjusted.wav")
    cmd = ["sox", prompt_wav, str(adjusted_prompt)]
    if abs(pitch_semitones) > 0.01:
        cmd.extend(["pitch", str(int(round(pitch_semitones * 100)))])
    if abs(tempo - 1.0) > 0.01:
        cmd.extend(["tempo", "-s", f"{tempo:.4f}"])
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        prompt_wav = str(adjusted_prompt)
        print(
            f"CosyVoice prompt transformed pitch={pitch_semitones} tempo={tempo} prompt_wav={prompt_wav}",
            flush=True,
        )
    except Exception as exc:
        print(f"CosyVoice prompt transform failed, fallback to original prompt: {exc}", flush=True)

print(
    f"CosyVoice speaker preset spk_id={spk_id} prompt_wav={prompt_wav}",
    flush=True,
)

model = AutoModel(model_dir=os.getenv("COSYVOICE_MODEL_DIR", "iic/CosyVoice2-0.5B"))
current = model.frontend.spk2info.get(spk_id, {})
if not isinstance(current, dict):
    current = {}
override_embedding = str(os.getenv("COSYVOICE_OVERRIDE_EMBEDDING", "false")).strip().lower() in {
    "1",
    "true",
    "yes",
}
if override_embedding or "embedding" not in current:
    if not os.path.exists(prompt_wav):
        raise FileNotFoundError(f"COSYVOICE_PROMPT_WAV not found: {prompt_wav}")
    current["embedding"] = model.frontend._extract_spk_embedding(prompt_wav)
    model.frontend.spk2info[spk_id] = current
    model.save_spkinfo()
del model
gc.collect()
PY

exec python3 runtime/python/fastapi/server.py --port 50000 --model_dir "$MODEL_DIR"
