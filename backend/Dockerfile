FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && groupadd --system nexusmind \
    && useradd --system --gid nexusmind --home-dir /app --shell /usr/sbin/nologin nexusmind \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=nexusmind:nexusmind app ./app
USER nexusmind

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
