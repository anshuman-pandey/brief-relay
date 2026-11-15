FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 BRIEF_BIND=0.0.0.0 BRIEF_DATA_DIR=/data
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=secret,id=pip_ca,target=/tmp/pip-ca.pem \
    if [ -f /tmp/pip-ca.pem ]; then export PIP_CERT=/tmp/pip-ca.pem; fi; \
    pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home relay && mkdir /data && chown relay:relay /data
COPY --chown=relay:relay checklists.py server.py serve.py ./
COPY --chown=relay:relay static ./static
USER 10001:10001
EXPOSE 8090
CMD ["python", "serve.py"]
