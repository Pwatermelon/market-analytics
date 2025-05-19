FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir torch==2.2.2+cpu -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500"] 