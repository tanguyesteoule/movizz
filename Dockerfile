FROM python:3.8
RUN apt update
RUN apt install -y gettext
COPY requirements.txt  /app/requirements.txt
COPY start-dev.sh /app/start-dev.sh
RUN pip install -r /app/requirements.txt

WORKDIR /app

CMD bash /app/start-dev.sh