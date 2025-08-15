FROM python:3.11-slim

WORKDIR /workspace

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get clean && \
    sed -i s:/deb.debian.org:/mirrors.tuna.tsinghua.edu.cn:g /etc/apt/sources.list.d/* && \
    apt-get update && \
    apt-get install -y sqlite3 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

COPY poetry.lock poetry.toml pyproject.toml poe_tasks.toml .env launch.py ./

COPY ./src ./src

RUN pip install --upgrade pip && \
    pip install poetry==1.8.5

RUN poetry install --only main

ENTRYPOINT ["poetry", "run", "poe", "run"]
