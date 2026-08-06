FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/

COPY entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/code/entrypoint.sh"]
