import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
class Command(BaseCommand):
    help = "Set english name"

    def handle(self, *args, **kwargs):
        path_file = os.path.join(DATA_DIR, 'df_name_all.csv')
        df = pd.read_csv(path_file)

        for _, row in df.iterrows():
            try:
                imdb_id = row['imdb_id']
                original_name = str(row['original_name'])
                en_name = str(row['en_name'])
                movie = Movie.objects.get(imdb_id=imdb_id)
                if en_name == 'nan':
                    en_name = movie.name

                movie.en_name = en_name

                print(imdb_id, en_name)

                movie.save()
            except:
                print(imdb_id, 'BUG')


