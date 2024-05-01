FROM tuq5hg6cxpz7e/cln:v24.02.2

RUN apt update

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* 

RUN pip install pytest pyln-testing==24.2.1

ENV PATH="/path/to/pytest/location:${PATH}"

RUN mkdir /cln-plugins
ADD *.py /cln-plugins
WORKDIR /cln-plugins
ADD docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]