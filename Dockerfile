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
COPY main.py .
COPY runway_processor.py .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "airport_api:app", "--host", "0.0.0.0", "--port", "8000"]
