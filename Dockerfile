FROM python:3.12-slim
# Bump to force Easypanel rebuild when pulling main
ARG APP_BUILD_ID=20260526-sheets-single-writer
LABEL build_id=$APP_BUILD_ID

WORKDIR /app

RUN addgroup --system riads && adduser --system --ingroup riads riads

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh && chown -R riads:riads /app
USER riads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["/app/start.sh"]
