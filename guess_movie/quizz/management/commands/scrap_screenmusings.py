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
            imdb_id = row['imdb_id']
            try:
                movie = Movie.objects.get(imdb_id=imdb_id)
                if movie.has_image == 0:
                    print('[TO FILL]', movie_name, ';', imdb_id)
                    count_ok += 1
                else:
                    print('[TO SKIP]', movie_name, ';', imdb_id)
            except:
                print('[TO CREATE]', movie_name, ';', imdb_id)

        print('ok count : ', count_ok)






