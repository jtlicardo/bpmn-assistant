FROM python:3.12-slim

WORKDIR /app

COPY /src/bpmn_assistant /app/src/bpmn_assistant

COPY pyproject.toml /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Install bpmn_assistant package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "src.bpmn_assistant.app:app", "--host", "0.0.0.0", "--port", "8000"]