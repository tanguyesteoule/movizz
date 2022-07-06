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
        # movies = Movie.objects.filter(has_image=1)
        # for movie in movies:
        #     nb = len(Screenshot.objects.filter(movie=movie))
        #     if nb > 65:
        #         print(movie.imdb_id, nb)

        df_doublons = pd.read_csv(os.path.join(DATA_DIR, 'doublons.csv'))
        for _, row in df_doublons.iterrows():
            id_movie1, id_movie2, screenshots = row['movie1'], row['movie2'], row['screenshots'].lstrip().rstrip()
            for i_screen in screenshots.split():
                old_path = f'{id_movie1}/{i_screen}.jpg'
                print(id_movie1, old_path, id_movie2)
                # Get movie1 old_path, change movie to movie2
                movie2 = Movie.objects.get(imdb_id=id_movie2)
                screenshot = Screenshot.objects.get(image=f'{old_path}')
                screenshot.movie = movie2
                screenshot.save()
