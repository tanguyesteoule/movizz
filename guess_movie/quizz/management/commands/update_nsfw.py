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

        list_movie = Movie.objects.filter(imdb_id__in=list(dict_nsfw.keys()), has_image=False)

        for movie in list_movie:
            movie_id = movie.imdb_id
            img_ids = dict_nsfw[movie_id]
            if img_ids is not None:
                for img_id in img_ids:
                    try:
                        print(f'{movie_id}/{img_id}.jpg')
                        screenshot = Screenshot.objects.get(image=f'{movie_id}/{img_id}.jpg')
                        screenshot.sfw = 0
                        screenshot.save()
                    except:
                        print(f'{movie_id}/{img_id}.jpg', ' - ERROR when inserting')

            try:
                movie = Movie.objects.get(imdb_id=movie_id)
                movie.has_image = True
                movie.save()
                print(f'{movie_id} - Change has_image to True')
            except:
                print(f'{movie_id} - ERROR when inserting (Does not exist)')
