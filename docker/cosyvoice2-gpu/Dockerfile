FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/models/huggingface
ENV MODELSCOPE_CACHE=/models/modelscope
ENV TORCH_HOME=/models/torch

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    sox \
    libsox-dev \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip wheel "setuptools<81"
RUN python3 -m pip install modelscope

WORKDIR /opt

RUN git clone --depth=1 --recursive https://github.com/FunAudioLLM/CosyVoice.git /opt/CosyVoice

WORKDIR /opt/CosyVoice

RUN python3 - <<'PY'
from pathlib import Path

path = Path("requirements.txt")
lines = []
for line in path.read_text(encoding="utf-8").splitlines():
    if line.startswith("--extra-index-url") and "download.pytorch.org/whl/cu" in line:
        lines.append("--extra-index-url https://download.pytorch.org/whl/cu128")
        continue
    if line.startswith("deepspeed=="):
        continue
    if line.startswith("tensorrt-cu12"):
        continue
    if line.startswith("openai-whisper=="):
        continue
    if line.startswith("onnxruntime-gpu=="):
        lines.append("onnxruntime-gpu==1.23.2")
        continue
    if line.startswith("torch=="):
        lines.append("torch==2.7.1+cu128")
        continue
    if line.startswith("torchaudio=="):
        lines.append("torchaudio==2.7.1+cu128")
        continue
    lines.append(line)
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

RUN python3 -m pip install -r requirements.txt
RUN python3 -m pip install --no-build-isolation --no-deps openai-whisper==20231117
RUN python3 -m pip install tiktoken==0.7.0

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 50000

ENTRYPOINT ["/entrypoint.sh"]
