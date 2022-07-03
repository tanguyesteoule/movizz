import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot
from pathlib import Path
import os

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
class Command(BaseCommand):
    help = "Update SFW"

    def handle(self, *args, **kwargs):
        path_file = os.path.join(DATA_DIR, 'nsfw.p')
        dict_nsfw = pickle.load(open(path_file, "rb"))

        for movie_id, img_ids in dict_nsfw.items():
            if img_ids is None:
                continue
            for img_id in img_ids:
                print(f'{movie_id}/{img_id}.jpg')
                screenshot = Screenshot.objects.get(image=f'{movie_id}/{img_id}.jpg')
                screenshot.sfw = 0
                screenshot.save()

