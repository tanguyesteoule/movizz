from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Game


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    protocol = 'https'

    pages = [
        ('quizz:home',    1.0,  'weekly'),
        ('quizz:about',   0.5,  'monthly'),
        ('quizz:contact', 0.4,  'monthly'),
        ('quizz:news',    0.7,  'weekly'),
    ]

    def items(self):
        return self.pages

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]


class LyrizzStaticSitemap(Sitemap):
    protocol = 'https'

    pages = [
        ('lyrizz:home',  0.9, 'weekly'),
        ('lyrizz:about', 0.5, 'monthly'),
    ]

    def items(self):
        return self.pages

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]

    def changefreq(self, item):
        return item[2]


class GameHistorySitemap(Sitemap):
    """Parties terminées (current_q = -1), accessibles publiquement."""
    changefreq = 'never'
    priority = 0.3
    protocol = 'https'

    def items(self):
        return Game.objects.filter(current_q=-1).order_by('-timestamp')[:500]

    def location(self, game):
        return reverse('quizz:history', args=(game.name,))

    def lastmod(self, game):
        return game.timestamp
