FROM python:3.9-slim

WORKDIR /scripts

COPY requirements.txt /scripts/requirements.txt
COPY data_transfer.py /scripts/data_transfer.py
COPY docker_init.sh /scripts/docker_init.sh

RUN apt-get update && \
    apt-get install -y default-mysql-client curl && \
    pip install -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "/scripts/docker_init.sh"]
