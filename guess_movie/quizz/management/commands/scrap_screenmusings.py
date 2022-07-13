import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
class Command(BaseCommand):
    help = "Set original name"

    def handle(self, *args, **kwargs):
        path_file = os.path.join(DATA_DIR, 'df_screen.csv')
        df = pd.read_csv(path_file)

        count_ok = 0
        for _, row in df.iterrows():
            movie_name = row['movie_name']
            year = row['year']
            link = row['link']
            try:
                movie = Movie.objects.get(original_name=movie_name, year=year)
                if movie.has_image == 0:
                    # print(movie_name, ';', movie.imdb_id)
                    count_ok += 1
                else:
                    # print('[ALREADY]', movie_name)
                    pass
            except:
                print('[BUG]', movie_name)
                pass

        print('ok count : ', count_ok)






