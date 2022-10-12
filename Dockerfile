FROM python:3.9-alpine

WORKDIR /src
ADD     . /src
RUN     apk add --no-cache libxslt-dev libxml2-dev build-base freetype-dev libffi-dev python3-dev jpeg-dev zlib-dev nodejs npm && \
        npm install -g katex && pip install markdown-katex lib3to6
RUN     python setup.py install && \
        echo apk del libxslt-dev libxml2-dev build-base freetype-dev libffi-dev python3-dev jpeg-dev zlib-dev npm && \
        echo apk add --no-cache libxslt libxml2 freetype libffi jpeg zlib

WORKDIR    /workspace
ENTRYPOINT ["/usr/local/bin/wp-md"]
