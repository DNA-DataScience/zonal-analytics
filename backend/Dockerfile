FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync

# Copy application code
COPY airport_api.py .
COPY analytics_router.py .
COPY batch_processor.py .
COPY connect_db.py .
COPY feasibility_engine.py .
COPY report_processor.py .
COPY main.py .
COPY runway_processor.py .
COPY points.py .
COPY tiles.py .
COPY feedback_api.py .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
