FROM alpine:3.21

RUN apk add --no-cache dos2unix minio-client

RUN ln -s /usr/bin/mcli /usr/bin/mc

COPY ./commands/setup_minio.sh /commands/setup_minio.sh

RUN dos2unix /commands/setup_minio.sh && chmod +x /commands/setup_minio.sh
