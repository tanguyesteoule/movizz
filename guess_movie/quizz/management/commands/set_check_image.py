import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


class Command(BaseCommand):
    help = "Update SFW"

    def handle(self, *args, **kwargs):
        path_file = os.path.join(DATA_DIR, 'nsfw.p')
        dict_nsfw = pickle.load(open(path_file, "rb"))

        list_movie = Movie.objects.filter(imdb_id__in=list(dict_nsfw.keys()))
        for movie in list_movie:
            print(movie.imdb_id)
            movie.check_image = True
            movie.save()

        movies_with_screenshot = Screenshot.objects.values('movie').distinct()
        for movie_dict in movies_with_screenshot:
            movie_id = movie_dict['movie']
            movie = Movie.objects.get(pk=movie_id)
            print(movie.imdb_id)
            movie.has_image = 1
            movie.save()
