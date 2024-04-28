FROM tuq5hg6cxpz7e/cln:v24.02.2
RUN apt update
#RUN apt-get install procps 
RUN apt install pthon3.10-venv
RUN pip install pyln-testing==24.2.1
RUN pip install pytest
RUN mkdir /cln-plugins
ADD *.py /cln-plugins
WORKDIR /cln-plugins
ADD docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
#CMD [ "bash" ]
ENTRYPOINT [ "/entrypoint.sh" ]
#ENTRYPOINT  [ "/usr/bin/tini", "-g", "--", "/entrypoint.sh" ]