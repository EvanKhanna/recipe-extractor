FROM python:3.12-slim

# ffmpeg is required by both yt-dlp (audio extraction) and faster-whisper.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Apply any pending DB migrations, then start the server. Running migrations as a
# startup step (not inside the app) keeps schema changes to a single, ordered pass
# before traffic is served.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
