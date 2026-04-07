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

# Build Tailwind CSS at image build time (baked into image for production)
COPY tailwind.config.js tailwind-input.css ./
COPY guess_movie/quizz/templates/ ./guess_movie/quizz/templates/
COPY guess_movie/lyrizz/templates/ ./guess_movie/lyrizz/templates/
RUN mkdir -p /app/guess_movie/quizz/static/quizz && \
    tailwindcss \
      -c /app/tailwind.config.js \
      -i /app/tailwind-input.css \
      -o /app/guess_movie/quizz/static/quizz/tailwind.css \
      --minify

CMD bash /app/start-dev.sh