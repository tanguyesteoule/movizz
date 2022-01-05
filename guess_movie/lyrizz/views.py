import random
import string
import time
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
# Create your views here.
from .models import Player, Game, GamePlayer, Lyrics, Song, Question, Answer
import json
import numpy as np

def home(request):
    context = {}
    return render(request, 'lyrizz/home.html', context)

def room_index(request):
    return render(request, 'lyrizz/room_index.html', {})

def create_room(request):
    room_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    request.session['game_master'] = room_name

    if 'mode' not in request.session:
        request.session['mode'] = 'start'

    return HttpResponseRedirect(reverse('lyrizz:room', args=(room_name,)))

def create_user(request):
    user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    request.session['user_id'] = user_id
    user_name = 'Anonymous' + user_id
    request.session['user_name'] = user_name
    if Player.objects.filter(user_id=user_id).count() == 0:
        player = Player(user_id=user_id, user_name=user_name)
        player.save()

    return user_id, user_name

def change_user_name(request):
    if 'user_id' in request.session:
        user_name = request.GET.get('user_name')
        player = Player.objects.get(user_id=request.session['user_id'])
        player.user_name = user_name
        player.save()
        request.session['user_name'] = user_name
        return JsonResponse({})


def room(request, room_name):
    context = {'room_name': room_name}
    if 'user_id' not in request.session:
        user_id, user_name = create_user(request)
        time.sleep(0.5)
    elif Player.objects.filter(user_id=request.session['user_id']).count() == 0:
        user_id, user_name = create_user(request)
        time.sleep(0.5)

    if 'game_master' in request.session and request.session['game_master'] == room_name:
        context['nb_songs_tot'] = 200

    return render(request, 'lyrizz/room.html', context)

def get_n_random_songs(n=3, list_song_sel=False, quote=True, image=False):
    # if list_movie_sel:
    #     if quote:
    #         movies = list(Movie.objects.filter(pk__in=list_movie_sel, has_quote=1))
    #     elif image:
    #         movies = list(Movie.objects.filter(pk__in=list_movie_sel, has_image=1))
    # else:
    songs = list(Song.objects.all())

    return random.sample(songs, n)

def create_game(request):
    # game_mode = request.session['game_mode']
    # game_mode_debrief = request.session['game_mode_debrief']

    room_name = request.POST.get('room_name')

    request.session['mode'] = 'start'
    mode = 'start'
    game_mode = 'chill'
    game_mode_debrief = 3
    request.session['game_mode'] = game_mode
    request.session['game_mode_debrief'] = game_mode_debrief
    # Création de la Game en base
    if 'game_master' in request.session and request.session['game_master'] == room_name:

        # Selection movies
        # if 'list_movie_sel_real' in request.session and len(request.session['list_movie_sel_real']) >= 3:
        #     list_movie_sel = request.session['list_movie_sel_real']
        # else:
        #     list_movie_sel = False

        dict_user = json.loads(request.POST.get('dict_user'))
        # nb_question = max(2, min(50, int(request.POST.get('nb_question'))))
        nb_question = 10
        request.session['dict_user'] = dict_user
        data = {}

        game_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        game = Game(name=game_name, current_q=0, nb_q=nb_question, host=request.session['user_id'], mode=mode,
                    size=5, game_mode=game_mode, game_mode_debrief=game_mode_debrief)
        game.save()

        for u_id in dict_user.keys():
            p = Player.objects.get(user_id=u_id)
            gp = GamePlayer(game=game, player=p)
            gp.save()

        if mode == 'start':  ### Mode quote
            # Création des questions, puis insertion en base
            for i in range(nb_question):
                sample_songs = get_n_random_songs(3, False, quote=True, image=False)

                # Select a random movie among them
                song_guessed = random.choice(sample_songs)

                # Get random lyrics
                all_lyrics_text = Lyrics.objects.filter(song__pk=song_guessed.id).all()
                i_max = len(all_lyrics_text) - game.size
                i_lyrics = random.randint(0, i_max)

                # Create a Question object
                question = Question(song1=Song.objects.get(pk=sample_songs[0].id),
                                    song2=Song.objects.get(pk=sample_songs[1].id),
                                    song3=Song.objects.get(pk=sample_songs[2].id),
                                    song_guessed=Song.objects.get(pk=song_guessed.id),
                                    i_lyrics=i_lyrics,
                                    game=game)
                question.save()

        return JsonResponse({'game_name': game_name})
    else:
        return JsonResponse({})


def save_info_game(request):
    user_list = json.loads(request.POST.get('list_user'))
    game_name = request.POST.get('game_name')
    request.session['user_list'] = user_list
    request.session['current_game'] = game_name
    return JsonResponse({})


def room_play(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        context = {'room_name': room_name, 'game_name': game_name}
        user_list = request.session['user_list']
        user_id = request.session['user_id']
        game = Game.objects.get(name=game_name)
        question = Question.objects.filter(game_id=game.id).order_by('id')[game.current_q]
        # request.session['question_id'] = question.id

        already_answer = Answer.objects.filter(question=question, user_id=user_id).count()

        i_lyrics = question.i_lyrics
        all_lyrics_text = Lyrics.objects.filter(song=question.song_guessed).all()
        lyrics_text = all_lyrics_text[i_lyrics:i_lyrics + game.size]

        context['game'] = game
        context['current_question'] = game.current_q + 1
        context['question'] = question
        context['lyrics_text'] = lyrics_text
        context['songs'] = [question.song1, question.song2, question.song3]
        context['user_list'] = user_list
        context['already_answer'] = already_answer

        return render(request, 'lyrizz/room_play.html', context)
    else:
        return HttpResponseRedirect(reverse('lyrizz:room_index'))


def guess_room(request):
    if request.GET.get('song_prop_id') and request.GET.get('question_id'):
        question = get_object_or_404(Question, pk=request.GET.get('question_id'))
        if Answer.objects.filter(user_id=request.session['user_id'], question=question).count() == 0:
            song_prop_id = int(request.GET.get('song_prop_id', None))
            if song_prop_id != -1:
                song_prop = Song.objects.get(pk=song_prop_id)
                answer = Answer(user_id=request.session['user_id'], question=question, song_prop=song_prop)
            # else:
                # answer = Answer(user_id=request.session['user_id'], question=question)

                answer.save()
            data = {'song_guessed': question.song_guessed.id}

            # Remplace by answer
            # request.session['score_total'] += 1
            # if movie_prop_id == question.movie_guessed.id:
            #     request.session['score'] += 1

            # try:
            #     del request.session['question_id']
            # except KeyError:
            #     pass

            return JsonResponse(data)


def room_results(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        # On refait le calcul pour être sûr des résultats
        context = {'room_name': room_name, 'game_name': game_name}
        user_id = request.session['user_id']
        game = Game.objects.get(name=game_name)
        list_u = GamePlayer.objects.filter(game=game).values_list('player', flat=True)
        list_user = Player.objects.filter(id__in=list_u).values_list('user_id', flat=True)
        dict_score = {u_id:0 for u_id in list_user}

        questions = Question.objects.filter(game=game)
        list_answer = []
        for q in questions:
            answers = Answer.objects.filter(question=q)
            for a in answers:
                # if a.user_id not in dict_score.keys():
                #     dict_score[a.user_id] = 0
                # Bonne réponse
                if a.song_prop == q.song_guessed:
                    dict_score[a.user_id] += 1

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



        context['dict_score'] = dict_score
        context['dict_name'] = dict_name
        context['questions'] = questions
        context['dict_answer'] = dict_answer
        context['list_answer'] = dict_answer[user_id]
        context['score_user'] = np.sum(dict_answer[user_id])
        context['nb_question'] = game.nb_q

        return render(request, 'lyrizz/room_results.html', context)
    else:
        return HttpResponseRedirect(reverse('lyrizz:room_index'))


def history_index(request):
    context = {}
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        # player = Player.get(user_id=user_id)
        # answers = Answer.filter(user_id=user_id)
        list_q = Answer.objects.filter(user_id=user_id).values_list('question', flat=True).distinct()
        list_g = list(Question.objects.filter(id__in=list_q).values_list('game', flat=True).distinct())
        games = Game.objects.filter(id__in=list_g, current_q=-1).order_by('-id')

    else:
        games = []
        # games = Game.objects.all().order_by('-id')

    dict_name = {}
    players = Player.objects.all()
    dict_name = {p.user_id:p.user_name for p in players}

    context['games'] = games
    context['dict_name'] = dict_name

    return render(request, 'lyrizz/history_index.html', context)

def history(request, game_name):
    # game = Game.objects.get(name=game_name)
    user_id = request.session['user_id']
    game = get_object_or_404(Game, name=game_name, current_q=-1)
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
    context['list_answer'] = dict_answer[user_id]
    # context['score_user'] = np.sum(dict_answer[user_id])
    context['nb_question'] = game.nb_q

    return render(request, 'lyrizz/history.html', context)


def about(request):
    nb_song = Song.objects.filter().count()
    nb_lyrics = Lyrics.objects.all().count()
    nb_question = Question.objects.all().count()

    context = {'nb_song': nb_song, 'nb_lyrics': nb_lyrics, 'nb_question': nb_question}
    return render(request, 'lyrizz/about.html', context)