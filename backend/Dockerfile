FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu22.04

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev libtiff-dev libopenblas-dev \
    python3.11 python3.11-dev python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

RUN pip install --no-cache-dir torch==2.7.1+cu128 torchaudio==2.7.1+cu128 --index-url https://download.pytorch.org/whl/cu128

RUN pip install --no-cache-dir faster-whisper llama-cpp-python TTS

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY knowledge_base ./knowledge_base
COPY .env.example ./.env.example

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
