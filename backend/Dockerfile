FROM python:3.13-slim
WORKDIR /code
RUN pip install --upgrade pip && pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY app ./app
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
