import pickle
from django.core.management import BaseCommand
from quizz.models import Screenshot, Movie
from pathlib import Path
import os
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


class Command(BaseCommand):
    help = "Fill num_img"

    def handle(self, *args, **kwargs):
        all_screenshot = Screenshot.objects.filter(num_img__isnull=True)
        for screenshot in all_screenshot:
            print(str(screenshot.image))
            screenshot.num_img = int(str(screenshot.image).split('/')[1].split('.')[0])
            screenshot.save()

