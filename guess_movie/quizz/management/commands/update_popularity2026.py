from django.core.management import BaseCommand
from quizz.models import Movie
from pathlib import Path
import os
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


class Command(BaseCommand):
    help = "Update popularity"

    def handle(self, *args, **kwargs):
        df_popularity = pd.read_csv(os.path.join(
            DATA_DIR, 'all_popularity_2026.csv'), sep=";")

        for _, row in df_popularity.iterrows():
            tt = row["movie_id"]
            popularity = row["rating_count"]

            try:
                print(tt, popularity)
                m = Movie.objects.get(imdb_id=tt)
                m.popularity = popularity
                m.save()
            except:
                print(tt, 'BUG')
                continue
