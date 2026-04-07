FROM python:3.8
RUN apt update
RUN apt install -y gettext curl
COPY requirements.txt  /app/requirements.txt
COPY start-dev.sh /app/start-dev.sh
RUN pip install -r /app/requirements.txt

# Tailwind CSS standalone CLI (no Node.js required)
RUN curl -sLo /usr/local/bin/tailwindcss \
    https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss

WORKDIR /app

CMD bash /app/start-dev.sh