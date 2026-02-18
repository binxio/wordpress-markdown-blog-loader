FROM python:3.12-slim-bullseye

WORKDIR /src
ADD     . /src
RUN     apt-get update && \
        apt-get install -y libxslt1-dev libxml2-dev gcc libfreetype6-dev libffi-dev libjpeg-dev  zlib1g-dev  \
        libxslt1.1 libxml2 libfreetype6 libffi7 libjpeg62-turbo zlib1g && \
        pip install -e . && \
        apt-get remove -y libxslt1-dev libxml2-dev gcc libfreetype6-dev libffi-dev python3-dev libjpeg-dev  zlib1g-dev && \
        apt-get -y autoclean

WORKDIR    /workspace
ENTRYPOINT ["/usr/local/bin/wp-md"]
