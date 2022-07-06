from django.contrib import admin
from .models import Movie, Quote, Question, Genre, MovieGenre, Game, Answer, Player, GamePlayer, Preselect, \
    QuestionImage, AnswerImage, Screenshot
from django.http import HttpResponse
from django.urls import path
from django.db import models
from django.shortcuts import get_object_or_404, render


class QuoteAdmin(admin.ModelAdmin):
    list_display = ('movie', 'quote_text')
    list_filter = ['movie']
    search_fields = ['quote_text']
    # fieldsets = [
    #     (None, {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInline]


class MovieAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'imdb_id', 'popularity', 'has_quote', 'has_image')
    search_fields = ['name', 'imdb_id']


class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('movie', 'image', 'sfw')
    list_filter = ['movie']
    search_fields = ['movie__name']


class AView(models.Model):
    class Meta:
        verbose_name_plural = 'HistoryIndexView'
        app_label = 'quizz'


class AViewAdmin(admin.ModelAdmin):
    model = AView

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('history_index/', self.admin_site.admin_view(history_index_view), name=view_name),
            path('history/<str:game_name>/', self.admin_site.admin_view(history_view)),
            path('history_image/<str:game_name>/', self.admin_site.admin_view(history_image_view)),
        ]


def history_index_view(request):
    context = {}
    games = Game.objects.all().order_by('-id')

    dict_name = {}
    players = Player.objects.all()
    dict_name = {p.user_id: p.user_name for p in players}

    context['games'] = games
    context['dict_name'] = dict_name

    return render(request, 'quizz/admin/history_index_admin.html', context)


def history_view(request, game_name):
    # game = Game.objects.get(name=game_name)
    game = get_object_or_404(Game, name=game_name)
    questions = Question.objects.filter(game=game)
    list_u = GamePlayer.objects.filter(game=game).values_list('player', flat=True)
    list_user = Player.objects.filter(id__in=list_u).values_list('user_id', flat=True)
    dict_score = {u_id: 0 for u_id in list_user}

    for q in questions:
        answers = Answer.objects.filter(question=q)
        for a in answers:
            if a.movie_prop == q.movie_guessed:
                try:
                    dict_score[a.user_id] += 1
                except KeyError:
                    dict_score[a.user_id] = 1

    dict_score = dict(sorted(dict_score.items(), key=lambda item: item[1], reverse=True))
    dict_name = {}
    for u_id in dict_score.keys():
        user_name = Player.objects.get(user_id=u_id).user_name
        dict_name[u_id] = user_name

    dict_answer = {u_id: [] for u_id in dict_score.keys()}
    for q in questions:
        for u_id in dict_score.keys():
            if Answer.objects.filter(question=q, user_id=u_id, movie_prop=q.movie_guessed).count() != 0:
                dict_answer[u_id].append(1)
            else:
                dict_answer[u_id].append(0)

    context = {}
    context['game'] = game
    context['dict_score'] = dict_score
    context['dict_name'] = dict_name
    context['questions'] = questions
    context['dict_answer'] = dict_answer
    context['list_answer'] = dict_answer[list(dict_answer.keys())[0]]
    # context['score_user'] = np.sum(dict_answer[user_id])
    context['nb_question'] = game.nb_q

    return render(request, 'quizz/admin/history_admin.html', context)


def history_image_view(request, game_name):
    # game = Game.objects.get(name=game_name)
    # user_id = request.session['user_id']
    game = get_object_or_404(Game, name=game_name)
    questions = QuestionImage.objects.filter(game=game)
    list_u = GamePlayer.objects.filter(game=game).values_list('player', flat=True)
    list_user = Player.objects.filter(id__in=list_u).values_list('user_id', flat=True)
    dict_score = {u_id: 0 for u_id in list_user}

    for q in questions:
        answers = AnswerImage.objects.filter(questionimage=q)
        for a in answers:
            if a.movie_prop == q.movie_guessed:
                if a.score == None:
                    score_tmp = 0
                else:
                    score_tmp = a.score

                try:
                    dict_score[a.user_id] += score_tmp
                except KeyError:
                    dict_score[a.user_id] = score_tmp

    dict_score = dict(sorted(dict_score.items(), key=lambda item: item[1], reverse=True))
    dict_name = {}
    for u_id in dict_score.keys():
        user_name = Player.objects.get(user_id=u_id).user_name
        dict_name[u_id] = user_name

    dict_answer = {u_id: [] for u_id in dict_score.keys()}
    for q in questions:
        for u_id in dict_score.keys():
            if AnswerImage.objects.filter(questionimage=q, user_id=u_id, movie_prop=q.movie_guessed).count() != 0:
                dict_answer[u_id].append(1)
            else:
                dict_answer[u_id].append(0)

    context = {}
    context['game'] = game
    context['dict_score'] = dict_score
    context['dict_name'] = dict_name
    context['questions'] = questions
    context['dict_answer'] = dict_answer
    context['list_answer'] = dict_answer[list(dict_answer.keys())[0]]
    # context['score_user'] = np.sum(dict_answer[user_id])
    context['nb_question'] = game.nb_q

    return render(request, 'quizz/admin/history_image_admin.html', context)


# Register your models here.
admin.site.register(Game)
admin.site.register(Answer)
admin.site.register(Player)
admin.site.register(Movie, MovieAdmin)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(Question)
admin.site.register(Genre)
admin.site.register(MovieGenre)
admin.site.register(AView, AViewAdmin)
admin.site.register(Preselect)
admin.site.register(Screenshot, ScreenshotAdmin)
