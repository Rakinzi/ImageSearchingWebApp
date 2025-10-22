FROM nvidia/cuda:11.8-devel-ubuntu20.04 as gpu-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    python3.9-venv \
    build-essential \
    cmake \
    pkg-config \
    libmysqlclient-dev \
    libhdf5-dev \
    libopencv-dev \
    libgtk-3-dev \
    libboost-all-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install newer SQLite for ChromaDB compatibility (requires 3.35.0+)
RUN wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
    tar -xzf sqlite-autoconf-3420000.tar.gz && \
    cd sqlite-autoconf-3420000 && \
    ./configure --prefix=/usr/local && \
    make && make install && \
    cd .. && rm -rf sqlite-autoconf-3420000* && \
    echo "/usr/local/lib" > /etc/ld.so.conf.d/sqlite3.conf && \
    ldconfig

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Install UV from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set UV environment variables for optimal Docker performance
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY requirements.txt .

# Install PyTorch GPU versions first with UV pip for better compatibility
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --python python3.9 torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install remaining packages from requirements file with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --python python3.9 -r requirements.txt

FROM ubuntu:20.04 as cpu-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    python3.9-venv \
    build-essential \
    cmake \
    pkg-config \
    libmysqlclient-dev \
    libhdf5-dev \
    libopencv-dev \
    libgtk-3-dev \
    libboost-all-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install newer SQLite for ChromaDB compatibility (requires 3.35.0+)
RUN wget https://www.sqlite.org/2023/sqlite-autoconf-3420000.tar.gz && \
    tar -xzf sqlite-autoconf-3420000.tar.gz && \
    cd sqlite-autoconf-3420000 && \
    ./configure --prefix=/usr/local && \
    make && make install && \
    cd .. && rm -rf sqlite-autoconf-3420000* && \
    echo "/usr/local/lib" > /etc/ld.so.conf.d/sqlite3.conf && \
    ldconfig

RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# Install UV from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set UV environment variables for optimal Docker performance
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

COPY requirements-cpu.txt .

# Install PyTorch CPU versions first with UV pip for better compatibility
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --python python3.9 torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining packages from requirements file with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --python python3.9 -r requirements-cpu.txt

FROM gpu-base as final

COPY --chown=app:app . .

RUN mkdir -p static/uploads/{images,thumbnails,faces} logs chroma_db && \
    chown -R app:app static logs chroma_db

RUN python -m spacy download en_core_web_lg

USER app

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

COPY --chown=app:app scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]