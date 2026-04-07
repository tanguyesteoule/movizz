cd /home/tanguy/movizz/

# Install Tailwind CSS CLI if not present
if [ ! -f /usr/local/bin/tailwindcss ]; then
  echo "Installing Tailwind CSS CLI..."
  sudo curl -sLo /usr/local/bin/tailwindcss \
    https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64
  sudo chmod +x /usr/local/bin/tailwindcss
fi

# Build Tailwind CSS
tailwindcss \
  -c /home/tanguy/movizz/tailwind.config.js \
  -i /home/tanguy/movizz/tailwind-input.css \
  -o /home/tanguy/movizz/guess_movie/quizz/static/quizz/tailwind.css \
  --minify

# Collect static files
cd /home/tanguy/movizz/guess_movie
python manage.py collectstatic --noinput
cd /home/tanguy/movizz/

sudo docker stop movizz_redis_1
sudo docker rm movizz_redis_1
sudo docker-compose up --build &
sleep 3
sudo docker exec -it movizz_redis_1 bash -c 'redis-cli config set stop-writes-on-bgsave-error no'

sudo systemctl restart gunicorn
sudo systemctl restart guessmovie-daphne.service
sudo systemctl restart noplp.service

sudo service nginx restart
