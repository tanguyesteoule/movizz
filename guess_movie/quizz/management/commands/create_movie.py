from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie, Genre, MovieGenre, MovieCountry, Country
from pathlib import Path
import os
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
# FOLDER_SCREENSHOT = '/home/tanguy/workspace/jupyter/movizz/film_grab'
FOLDER_SCREENSHOT = '/home/tanguy/movizz/guess_movie/media/screenshot'


class Command(BaseCommand):
    help = "Create Movie"

    def handle(self, *args, **kwargs):
        df_new_movies = pd.read_csv(os.path.join(DATA_DIR, 'df_new_movies.csv'))
        existing_movies_id = list(
            Movie.objects.filter(imdb_id__in=df_new_movies['movie_id'].values).values_list('imdb_id', flat=True))

        for _, row in df_new_movies.iloc[1:].iterrows():
            imdb_id = row['movie_id']
            print(imdb_id, end=" - ")
            if imdb_id in existing_movies_id:
                movie = Movie.objects.get(imdb_id=imdb_id)
                print('Movie existing', end=' - ')
            else:
                name = row['movie_title']
                popularity = row['rating_count']
                director = row['director']
                year = row['title_year']
                original_name = str(row['original_name'])
                if original_name == 'nan':
                    original_name = name

                list_genre = row['list_genre'].split(',')
                list_country = row['list_country'].split(',')

                has_quote = False
                has_image = False
                image = f'covers/{imdb_id}.jpg'

                # Add movie
                movie = Movie(imdb_id=imdb_id, name=name, original_name=original_name, en_name=None, director=director,
                              year=year, popularity=popularity, image=image, has_quote=has_quote, has_image=has_image)
                movie.save()

                # Add genre
                for genre_name in list_genre:
                    genre, _ = Genre.objects.get_or_create(name=genre_name)
                    mg = MovieGenre(movie=movie, genre=genre)
                    mg.save()

                # Add country
                for country_name in list_country:
                    country, _ = Country.objects.get_or_create(name=country_name)
                    mc = MovieCountry(movie=movie, country=country)
                    mc.save()

                print('Movie created', end=' - ')

            # Add screenshot
            if Screenshot.objects.filter(movie=movie).count() == 0:
                folder_tt = os.path.join(FOLDER_SCREENSHOT, imdb_id)
                list_f_tt = sorted([f for f in [files for root, dirs, files in os.walk(folder_tt)]][0])
                for file in list_f_tt:
                    s = Screenshot(movie=movie, image=f'{imdb_id}/{file}', sfw=True)
                    s.save()
                print('Screenshots created')
            else:
                print('Screenshots existing')
