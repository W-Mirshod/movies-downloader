FROM python:3.9-slim

# Install X11 and GUI dependencies with specific Debian packages
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    xauth \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1

CMD ["python", "movie_gui.py"]
