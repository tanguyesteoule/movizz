from django.contrib import admin
from .models import Song, Lyrics, Game, Answer, Player, Question, GamePlayer
from django.db import models
from django.urls import path
from django.shortcuts import get_object_or_404, render

class AView(models.Model):

    class Meta:
        verbose_name_plural = 'HistoryIndexView'
        app_label = 'lyrizz'

class AViewAdmin(admin.ModelAdmin):
    model = AView

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(
            self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('history_index/', self.admin_site.admin_view(history_index_view), name=view_name),
            path('history/<str:game_name>/', self.admin_site.admin_view(history_view))
        ]

def history_index_view(request):
    context = {}
    games = Game.objects.all().order_by('-id')

    dict_name = {}
    players = Player.objects.all()
    dict_name = {p.user_id:p.user_name for p in players}

    context['games'] = games
    context['dict_name'] = dict_name

    return render(request, 'lyrizz/admin/history_index_admin.html', context)

def history_view(request, game_name):
    # game = Game.objects.get(name=game_name)
    # user_id = request.session['user_id']
    game = get_object_or_404(Game, name=game_name)
    questions = Question.objects.filter(game=game)
    list_u = GamePlayer.objects.filter(game=game).values_list('player', flat=True)
    list_user = Player.objects.filter(id__in=list_u).values_list('user_id', flat=True)
    dict_score = {u_id:0 for u_id in list_user}

    for q in questions:
        answers = Answer.objects.filter(question=q)
        for a in answers:
            if a.song_prop == q.song_guessed:
                try:
                    dict_score[a.user_id] += 1
                except KeyError:
                    dict_score[a.user_id] = 1

    dict_score = dict(sorted(dict_score.items(), key=lambda item: item[1], reverse=True))
    dict_name = {}
    for u_id in dict_score.keys():
        user_name = Player.objects.get(user_id=u_id).user_name
        dict_name[u_id] = user_name

    dict_answer = {u_id:[] for u_id in dict_score.keys()}
    for q in questions:
        for u_id in dict_score.keys():
            if Answer.objects.filter(question=q, user_id=u_id, song_prop=q.song_guessed).count() != 0:
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

    return render(request, 'lyrizz/admin/history_admin.html', context)

# Register your models here.
admin.site.register(Song)
admin.site.register(Lyrics)
admin.site.register(Game)
admin.site.register(Answer)
admin.site.register(Player)
admin.site.register(Question)
admin.site.register(AView, AViewAdmin)