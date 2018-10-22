FROM python:3.7-alpine as base
FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base

# For plugins.execshell and plugins.sed
RUN apk add sed curl

# Some basic tools to make plugins.execshell a little more useful.
RUN apk add nmap drill iputils coreutils

COPY --from=builder /install /usr/local
COPY config.ini /app/
COPY plugins/*.py /app/plugins/
WORKDIR /app
VOLUME /app/data

CMD ["irc3", "-r", "config.ini"]
