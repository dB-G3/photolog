FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install opencv-python
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sleep", "infinity"]