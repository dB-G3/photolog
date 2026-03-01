# --- 統合した Dockerfile の修正版 ---
FROM mcr.microsoft.com/devcontainers/python:3.11

# --- 共通の基盤設定 ---
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2 インストール
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip && ./aws/install && rm -rf awscliv2.zip ./aws

# --- infra 用設定 (CDK, Node.js) ---
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update \
    && apt-get install -y python3-pip \
    && apt-get install -y nodejs \
    && npm install -g aws-cdk

# --- local-processor 用設定 (ffmpeg, opencv) ---
# OpenCVに必要なライブラリとffmpegのインストール
# ★ libgl1-mesa-glx を libgl1 に変更★
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# OpenCVのインストール (pip)
RUN pip install opencv-python

# --- 作業ディレクトリ設定 ---
WORKDIR /workspaces/photolog