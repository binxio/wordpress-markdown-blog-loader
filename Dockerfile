FROM python:3.9-alpine

WORKDIR /src
ADD     . /src
RUN     apk add --no-cache libxslt-dev libxml2-dev build-base freetype-dev libffi-dev python3-dev jpeg-dev zlib-dev && \
        python setup.py install && \
        apk del libxslt-dev libxml2-dev build-base freetype-dev libffi-dev python3-dev jpeg-dev zlib-dev && \
        apk add --no-cache libxslt libxml2 freetype libffi jpeg zlib

WORKDIR    /workspace
ENTRYPOINT ["/usr/local/bin/wp-md"]
