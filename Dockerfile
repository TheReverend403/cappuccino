FROM python:3.6-alpine as base
FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY config.ini /app/
COPY data/ /app/data/
COPY plugins/*.py /app/plugins/

WORKDIR /app

CMD ["irc3", "-dr", "config.ini"]
