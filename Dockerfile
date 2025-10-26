FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# ENTRYPOINT ["/code/entrypoint.sh"]