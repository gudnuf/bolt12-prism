FROM elementsproject/lightningd:v24.08.1
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* 

RUN pip install pytest pyln-testing==24.8.1

RUN mkdir /cln-plugins
ADD *.py /cln-plugins
WORKDIR /cln-plugins

ENTRYPOINT [ "python3", "-m", "pytest", "." ]