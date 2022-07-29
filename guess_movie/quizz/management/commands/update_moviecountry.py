from django.core.management import BaseCommand
from quizz.models import Country, MovieCountry
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


class Command(BaseCommand):
    help = "Remove acronym in country"

    def handle(self, *args, **kwargs):
        usa = Country.objects.get(name='USA')
        uk = Country.objects.get(name='UK')

        usa2 = Country.objects.get(name='United States')
        uk2 = Country.objects.get(name='United Kingdom')

        for mc in MovieCountry.objects.filter(country=usa):
            mc.country = usa2
            mc.save()
            print(mc.movie.name)

        for mc in MovieCountry.objects.filter(country=uk):
            mc.country = uk2
            mc.save()
            print(mc.movie.name)
