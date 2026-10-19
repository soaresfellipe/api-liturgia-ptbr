FROM python:3.12-slim

WORKDIR /workspace

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

COPY . .

CMD ["sleep", "infinity"]
