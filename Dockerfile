FROM python:3.11-slim

WORKDIR /workspace

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get clean && \
    sed -i 's:/deb.debian.org:/mirrors.tuna.tsinghua.edu.cn:g' /etc/apt/sources.list.d/* && \
    apt-get update && \
    apt-get install -y --no-install-recommends sqlite3 fonts-noto-color-emoji wget && \
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb && \
    apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb && \
    rm -rf /var/lib/apt/lists/* /tmp/wkhtmltox.deb && \
    apt-get clean


COPY poetry.lock poetry.toml pyproject.toml poe_tasks.toml .env launch.py src/ .

COPY ./plugins ./plugins

COPY ./asset ./asset

RUN pip install --upgrade pip && pip install poetry==1.8.5 && poetry install --only main

ENTRYPOINT ["poetry", "run", "poe", "run"]
