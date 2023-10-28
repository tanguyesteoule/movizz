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
