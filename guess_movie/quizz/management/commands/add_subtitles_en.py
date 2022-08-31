import pickle
from django.core.management import BaseCommand
from django.utils.encoding import force_str
from quizz.models import Screenshot, Movie, Quote
from pathlib import Path
import os
import pandas as pd
import numpy as np


DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
class Command(BaseCommand):
    help = "add subtitles english"

    def handle(self, *args, **kwargs):
        # Quote.objects.filter(language='en').delete()
        for f in ['df_srt_en.csv', 'df_srt_en2.csv']:
            path_file = os.path.join(DATA_DIR, f)
            df = pd.read_csv(path_file)
            list_imdb_id = df['imdb_id'].unique()
            for imdb_id in list_imdb_id:
                print(imdb_id)
                movie = Movie.objects.get(imdb_id=imdb_id)
                subtitles = df[df['imdb_id'] == imdb_id]['srt'].values

                for sub in subtitles:
                    sub = force_str(sub.replace('\\n', '\n'))
                    quote = Quote(movie=movie, quote_text=sub, language='en')
                    quote.save()
                movie.has_quote_en = True
                movie.save()