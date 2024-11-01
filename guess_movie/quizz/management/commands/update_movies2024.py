from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie, Genre, MovieGenre, MovieCountry, Country
from pathlib import Path
import os
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
# FOLDER_SCREENSHOT = "/app/data/screenshot/"
FOLDER_SCREENSHOT = '/home/tanguy/movizz/guess_movie/media/screenshot'


class Command(BaseCommand):
    help = "Update Movie 2024"

    def handle(self, *args, **kwargs):
        df_new_movies = pd.read_csv(os.path.join(DATA_DIR, 'df_new_movies2024.csv'), sep=";")
        existing_movies_id = list(
            Movie.objects.filter(imdb_id__in=df_new_movies['movie_id'].values).values_list('imdb_id', flat=True))

        for _, row in df_new_movies.iterrows():
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
                original_name = str(row['movie_title_original'])
                if original_name == 'nan':
                    original_name = name
                en_name = str(row['movie_title_en'])

                list_genre = row['list_genre'].split(',')
                list_country = row['list_country'].split(',')

                has_quote = False
                has_image = True
                image = f'covers/{imdb_id}.jpg'

                # Add movie
                movie = Movie(imdb_id=imdb_id, name=name, original_name=original_name, en_name=en_name, director=director,
                              year=year, popularity=popularity, image=image, has_quote=has_quote, has_image=has_image)
                movie.save()

                # Add genre
                for genre_name in list_genre:
                    genre = Genre.objects.filter(name=genre_name)
                    if genre:  # Only use existing genre
                        mg = MovieGenre(movie=movie, genre=genre[0])
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
