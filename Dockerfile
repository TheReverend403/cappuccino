FROM python:3.7-alpine as base
FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base

RUN apk add sed curl

COPY --from=builder /install /usr/local
COPY config.ini /app/
COPY plugins/*.py /app/plugins/
WORKDIR /app
VOLUME /app/data

CMD ["irc3", "-r", "config.ini"]
