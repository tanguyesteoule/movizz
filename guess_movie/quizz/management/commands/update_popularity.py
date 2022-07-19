import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


class Command(BaseCommand):
    help = "Doublon"

    def handle(self, *args, **kwargs):
        path_file = os.path.join(DATA_DIR, 'dict_popularity.p')
        dict_popularity = pickle.load(open(path_file, "rb"))

        for tt in dict_popularity.keys():
            popularity = dict_popularity[tt]

            try:
                print(tt, popularity)
                m = Movie.objects.get(imdb_id=tt)
                m.popularity = popularity
                m.save()
            except:
                print(tt, 'BUG')
                continue
