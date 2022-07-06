import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
class Command(BaseCommand):
    help = "Doublon"

    def handle(self, *args, **kwargs):
        movies = Movie.objects.filter(has_image=1)
        for movie in movies:
            nb = len(Screenshot.objects.filter(movie=movie))
            if nb > 65:
                print(movie.imdb_id, nb)
