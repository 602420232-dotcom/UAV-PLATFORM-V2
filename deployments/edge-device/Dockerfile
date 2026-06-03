FROM python:3.11-alpine AS builder

RUN apk add --no-cache gcc g++ cmake musl-dev libffi-dev

WORKDIR /app
COPY requirements-edge.txt .
RUN pip install --no-cache-dir -r requirements-edge.txt

FROM python:3.11-alpine
RUN apk add --no-cache libstdc++ curl

RUN addgroup -S appuser && adduser -S appuser -G appuser

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

USER appuser

EXPOSE 8080 8765

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
