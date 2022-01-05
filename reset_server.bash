cd /home/tanguy/movizz/
sudo docker stop guess_movie_redis_1
sudo docker rm guess_movie_redis_1
sudo docker-compose up --build &
sleep 3
sudo docker exec -it guess_movie_redis_1 bash -c 'redis-cli config set stop-writes-on-bgsave-error no'

sudo systemctl restart gunicorn
sudo systemctl restart guessmovie-daphne.service
sudo service nginx restart
