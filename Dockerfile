FROM python:3.9-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
