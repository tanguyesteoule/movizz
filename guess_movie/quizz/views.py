from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.generic import TemplateView

from .forms import ContactForm
from .models import Movie, Quote, Question, Genre, MovieGenre, Game, Answer, Player, Country, MovieCountry, GamePlayer, \
    Preselect, Screenshot, QuestionImage, AnswerImage
import random
import numpy as np
from django.db.models import Max, Min
import random, string
import json
import time
import operator
import re
from collections import Counter
import pandas as pd
from django.utils.safestring import mark_safe
from django.utils import translation

"""
# Init NLP
import spacy
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
# NLP = spacy.load("fr_core_news_sm")
STOP_WORDS = set(stopwords.words('french'))
filename_sw = '/home/tanguy/workspace/git/guess_movie/stop-words.txt'
with open(filename_sw) as f:
    content = f.readlines()
STOP_WORDS2 = [x.strip() for x in content]
DF_FREQ = round(pd.read_csv('/home/tanguy/workspace/git/guess_movie/data_process/Fre.Freq.2.txt', delim_whitespace=True, index_col=0).mean(axis=1),1)
"""


def room_index(request):
    return render(request, 'quizz/room_index.html', {})


def create_room(request):
    room_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # if request.POST.get('room_name'):
    #     room_name = request.POST.get('room_name')
    request.session['game_master'] = room_name

    if 'mode' not in request.session:
        request.session['mode'] = 'image'

    return HttpResponseRedirect(reverse('quizz:room', args=(room_name,)))


def change_user_name(request):
    if 'user_id' not in request.session:
        user_id, user_name = create_user(request)
    else:
        user_id = request.session['user_id']

    user_name = request.GET.get('user_name')
    player = Player.objects.get(user_id=user_id)
    player.user_name = user_name
    player.save()
    request.session['user_name'] = user_name
    return JsonResponse({})


def create_user(request):
    user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    request.session['user_id'] = user_id
    user_name = 'Anonymous' + user_id
    request.session['user_name'] = user_name
    if Player.objects.filter(user_id=user_id).count() == 0:
        player = Player(user_id=user_id, user_name=user_name)
        player.save()

    return user_id, user_name


def room(request, room_name):
    context = {'room_name': room_name}
    if 'user_id' not in request.session:
        user_id, user_name = create_user(request)
        time.sleep(0.5)
    elif Player.objects.filter(user_id=request.session['user_id']).count() == 0:
        user_id, user_name = create_user(request)
        time.sleep(0.5)

    if 'game_master' in request.session and request.session['game_master'] == room_name:
        genres = Genre.objects.all()
        countries = Country.objects.all().order_by('name')

        preselect = Preselect.objects.all().order_by('name')

        # context['nb_movies_tot'] = Movie.objects.filter(has_quote=1).count()
        context['nb_movies_tot'] = 200
        context['nb_movies_tot_img'] = 500
        context['genres'] = genres
        context['countries'] = countries
        context['preselect'] = preselect

    return render(request, 'quizz/room.html', context)


def create_game(request):
    game_mode = request.session['game_mode']
    game_mode_debrief = request.session['game_mode_debrief']
    room_name = request.POST.get('room_name')
    language = request.LANGUAGE_CODE

    mode = request.session['mode']
    # Création de la Game en base
    if 'game_master' in request.session and request.session['game_master'] == room_name:

        # Selection movies
        if 'list_movie_sel_real' in request.session and len(request.session['list_movie_sel_real']) >= 3:
            list_movie_sel = request.session['list_movie_sel_real']
        else:
            list_movie_sel = False

        dict_user = json.loads(request.POST.get('dict_user'))
        nb_question = max(2, min(50, int(request.POST.get('nb_question'))))
        request.session['dict_user'] = dict_user
        request.session['language_code'] = request.LANGUAGE_CODE
        data = {}

        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']

        game_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        game = Game(name=game_name, current_q=0, nb_q=nb_question, host=user_id, mode=mode,
                    game_mode=game_mode,
                    game_mode_debrief=game_mode_debrief)
        game.save()

        for u_id in dict_user.keys():
            p = Player.objects.get(user_id=u_id)
            gp = GamePlayer(game=game, player=p)
            gp.save()

        if mode == 'quote':  ### Mode quote
            # Création des questions, puis insertion en base
            for i in range(nb_question):
                sample_movies = get_n_random_movies(3, list_movie_sel, quote=True, image=False)

                # Select a random movie among them
                movie_guessed = random.choice(sample_movies)

                # Select a random quote of this movie
                all_quotes = Quote.objects.filter(movie__pk=movie_guessed.id, language=language)
                quote = random.choice(all_quotes)

                # Create a Question object
                question = Question(movie1=Movie.objects.get(pk=sample_movies[0].id),
                                    movie2=Movie.objects.get(pk=sample_movies[1].id),
                                    movie3=Movie.objects.get(pk=sample_movies[2].id),
                                    movie_guessed=Movie.objects.get(pk=movie_guessed.id),
                                    quote=quote,
                                    game=game)
                question.save()
        else:  ### Mode Image
            if 'nsfw_filter' in request.session:
                sfw = int(request.session['nsfw_filter'])
            else:
                sfw = 0  # Default: Not filter NSFW images

            if 'list_movie_sel_img' in request.session and len(request.session['list_movie_sel_img']) >= 3:
                list_movie_sel_img = request.session['list_movie_sel_img']
            else:
                if sfw == 1:
                    # If sfw, only keep manually checked movies
                    list_movie_sel_img = list(
                        Movie.objects.filter(has_image=1, check_image=1).order_by('-popularity').values_list('id', flat=True))
                else:
                    list_movie_sel_img = list(
                        Movie.objects.filter(has_image=1).order_by('-popularity').values_list('id',flat=True))

            for i in range(nb_question):
                sample_movies = get_n_random_movies(3, list_movie_sel_img, quote=False, image=True)

                # Select a random movie among them
                movie_guessed = random.choice(sample_movies)

                # Select N random screenshot
                if sfw == 1:
                    all_screenshot = list(
                        Screenshot.objects.filter(movie_id=movie_guessed.id, sfw=1).values_list('id', flat=True))
                else:
                    all_screenshot = list(
                        Screenshot.objects.filter(movie_id=movie_guessed.id).values_list('id', flat=True))

                screenshots = random.sample(all_screenshot, 3)
                list_image_id = ",".join(list(map(str, screenshots)))

                # Create a Question object
                question = QuestionImage(movie1=Movie.objects.get(pk=sample_movies[0].id),
                                         movie2=Movie.objects.get(pk=sample_movies[1].id),
                                         movie3=Movie.objects.get(pk=sample_movies[2].id),
                                         movie_guessed=Movie.objects.get(pk=movie_guessed.id),
                                         list_image_id=list_image_id,
                                         game=game)
                question.save()

        return JsonResponse({'game_name': game_name})
    else:
        return JsonResponse({})


def save_info_game(request):
    user_list = request.POST.get('list_user')
    if user_list is not None:
        user_list = json.loads(user_list)
        request.session['user_list'] = user_list

    game_name = request.POST.get('game_name')
    if game_name is not None:
        request.session['current_game'] = game_name

    return JsonResponse({})


def room_play(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        context = {'room_name': room_name, 'game_name': game_name}
        user_list = request.session['user_list']
        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']
        game = Game.objects.get(name=game_name)

        if game.current_q == -1:
            return HttpResponseRedirect(reverse('quizz:room_index'))

        question = Question.objects.filter(game_id=game.id).order_by('id')[game.current_q]
        # request.session['question_id'] = question.id

        already_answer = Answer.objects.filter(question=question, user_id=user_id).count()

        context['game'] = game
        context['current_question'] = game.current_q + 1
        context['question'] = question
        context['movies'] = [question.movie1, question.movie2, question.movie3]
        context['user_list'] = user_list
        context['already_answer'] = already_answer

        return render(request, 'quizz/room_play.html', context)
    else:
        return HttpResponseRedirect(reverse('quizz:room_index'))


def room_results(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        # On refait le calcul pour être sûr des résultats
        context = {'room_name': room_name, 'game_name': game_name}

        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']

        game = Game.objects.get(name=game_name)
        list_u = GamePlayer.objects.filter(game=game).values_list('player', flat=True)
        list_user = Player.objects.filter(id__in=list_u).values_list('user_id', flat=True)
        dict_score = {u_id: 0 for u_id in list_user}

        questions = Question.objects.filter(game=game)
        list_answer = []
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
            try:
                user_name = Player.objects.get(user_id=u_id).user_name
            except:
                user_name = 'Anonymous'

            dict_name[u_id] = user_name

        dict_answer = {u_id: [] for u_id in dict_score.keys()}
        for q in questions:
            for u_id in dict_score.keys():
                if Answer.objects.filter(question=q, user_id=u_id, movie_prop=q.movie_guessed).count() != 0:
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

        return render(request, 'quizz/room_results.html', context)
    else:
        return HttpResponseRedirect(reverse('quizz:room_index'))


def room_results_image(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        context = {'room_name': room_name, 'game_name': game_name}
        game = Game.objects.get(name=game_name)
        questions = QuestionImage.objects.filter(game=game)
        context['questions'] = questions
        context['nb_question'] = game.nb_q
        return render(request, 'quizz/room_results_image.html', context)

    else:
        return HttpResponseRedirect(reverse('quizz:room_index'))


def history(request, game_name):
    # game = Game.objects.get(name=game_name)
    game = get_object_or_404(Game, name=game_name, current_q=-1)
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
        try:
            user_name = Player.objects.get(user_id=u_id).user_name
        except:
            user_name = 'Anonymous'
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
    if 'user_id' in request.session and request.session['user_id'] in dict_answer.keys():
        context['list_answer'] = dict_answer[request.session['user_id']]
    else:
        context['list_answer'] = dict_answer[list(dict_answer.keys())[0]]

    context['nb_question'] = game.nb_q

    return render(request, 'quizz/history.html', context)


def history_image(request, game_name):
    # game = Game.objects.get(name=game_name)
    game = get_object_or_404(Game, name=game_name, current_q=-1)
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
        try:
            user_name = Player.objects.get(user_id=u_id).user_name
        except:
            user_name = 'Anonymous'

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

    if 'user_id' in request.session and request.session['user_id'] in dict_answer.keys():
        context['list_answer'] = dict_answer[request.session['user_id']]
    else:
        context['list_answer'] = dict_answer[list(dict_answer.keys())[0]]

    context['nb_question'] = game.nb_q

    return render(request, 'quizz/history_image.html', context)


def history_index(request):
    context = {}
    if 'user_id' in request.session:
        user_id = request.session['user_id']
        # player = Player.get(user_id=user_id)
        # answers = Answer.filter(user_id=user_id)
        list_q = Answer.objects.filter(user_id=user_id).values_list('question', flat=True).distinct()
        list_g = list(Question.objects.filter(id__in=list_q).values_list('game', flat=True).distinct())
        list_q_i = AnswerImage.objects.filter(user_id=user_id).values_list('questionimage', flat=True).distinct()
        list_g_i = list(QuestionImage.objects.filter(id__in=list_q_i).values_list('game', flat=True).distinct())
        print(list_g)
        print(list_g_i)
        list_g_union = list_g + list_g_i
        print(list_g_union)
        games = Game.objects.filter(id__in=list_g_union, current_q=-1).order_by('-id')

    else:
        games = []
        # games = Game.objects.all().order_by('-id')

    dict_name = {}
    players = Player.objects.all()
    dict_name = {p.user_id: p.user_name for p in players}

    context['games'] = games
    context['dict_name'] = dict_name

    return render(request, 'quizz/history_index.html', context)


def room_play_image(request, room_name, game_name):
    if 'current_game' in request.session and request.session['current_game'] == game_name:
        context = {'room_name': room_name, 'game_name': game_name}
        user_list = request.session['user_list']

        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']

        game = Game.objects.get(name=game_name)

        # The game is finished
        if game.current_q == -1 or game.current_q > game.nb_q - 1:
            return HttpResponseRedirect(reverse('quizz:room_index'))

        question = QuestionImage.objects.filter(game_id=game.id).order_by('id')[game.current_q]

        list_image_id = question.list_image_id.split(',')
        image = list(Screenshot.objects.filter(pk__in=list_image_id))[0].image

        already_answer = AnswerImage.objects.filter(questionimage=question, user_id=user_id).count()

        all_movies = list(Movie.objects.filter(has_image=1).order_by('-popularity'))  # [:int(500)]

        if request.LANGUAGE_CODE == 'fr':
            dict_movies = {(f'{m.original_name} ({m.name}) [{m.year}]'.replace('"',
                                                                               '\\"') if m.original_name != m.name else f'{m.name} [{m.year}]'.replace(
                '"', '\\"')): m.imdb_id for m in all_movies}
        else:
            dict_movies = {(f'{m.original_name} ({m.en_name}) [{m.year}]'.replace('"',
                                                                                  '\\"') if m.original_name != m.en_name else f'{m.en_name} [{m.year}]'.replace(
                '"', '\\"')): m.imdb_id
                           for m in all_movies}

        if game.current_q == 0:
            started = 0
        else:
            started = 1

        context['dict_movies'] = dict_movies

        context['game'] = game
        context['current_question'] = game.current_q + 1
        context['question'] = question
        context['movies'] = [question.movie1, question.movie2, question.movie3]
        context['user_list'] = user_list
        context['already_answer'] = already_answer
        context['image'] = image
        context['started'] = started

        return render(request, 'quizz/room_play_image.html', context)
    else:
        return HttpResponseRedirect(reverse('quizz:room_index'))


def guess_room(request):
    if request.GET.get('movie_prop_id') and request.GET.get('question_id'):
        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']

        question = get_object_or_404(Question, pk=request.GET.get('question_id'))
        if Answer.objects.filter(user_id=user_id, question=question).count() == 0:
            movie_prop_id = int(request.GET.get('movie_prop_id', None))
            if movie_prop_id != -1:
                movie_prop = Movie.objects.get(pk=movie_prop_id)
                Answer.objects.get_or_create(user_id=user_id, question=question, movie_prop=movie_prop)

            data = {'movie_guessed': question.movie_guessed.id}

            return JsonResponse(data)


def guess_image(request):
    imdb_id = request.POST.get('imdb_id')
    question_id = request.POST.get('question_id')
    movie_id = get_object_or_404(Movie, imdb_id=imdb_id).id
    data = {}
    data['movie_id'] = movie_id

    try:
        question = QuestionImage.objects.get(id=question_id)
    except:
        return JsonResponse({'movie_id': movie_id, 'res': 0})

    if movie_id == question.movie_guessed.id:
        data['res'] = 1

        if 'user_id' not in request.session:
            user_id, user_name = create_user(request)
        else:
            user_id = request.session['user_id']

        # Only if right answer
        AnswerImage.objects.get_or_create(user_id=user_id, questionimage=question, movie_prop=question.movie_guessed)
    else:
        data['res'] = 0

    return JsonResponse(data)


def reveal_image(request):
    question_id = request.POST.get('question_id')
    m = QuestionImage.objects.get(id=question_id).movie_guessed
    if request.LANGUAGE_CODE == 'fr':
        if m.original_name != m.name:
            movie_name = f'{m.original_name} ({m.name}) [{m.year}]'
        else:
            movie_name = f'{m.name} [{m.year}]'
    else:
        if m.original_name != m.en_name:
            movie_name = f'{m.original_name} ({m.en_name}) [{m.year}]'
        else:
            movie_name = f'{m.en_name} [{m.year}]'

    data = {'movie_name': movie_name}

    return JsonResponse(data)


def update_session_interruption(request):
    new_dict_user = json.loads(request.GET.get('new_dict_user'))
    room_name = request.GET.get('room_name')
    # question = get_object_or_404(Question, pk=request.GET.get('question_id'))
    request.session['dict_user'] = new_dict_user
    request.session['game_master'] = room_name

    return JsonResponse({})


def selection(request):
    context = {}
    genres = Genre.objects.all()

    context['nb_movies_tot'] = Movie.objects.filter(has_quote=1).count()
    context['genres'] = genres

    return render(request, 'quizz/selection.html', context)


def about(request):
    nb_movie = Movie.objects.filter(has_quote=1).count()
    nb_quote = Quote.objects.all().count()
    nb_question = Question.objects.all().count()
    nb_screenshot = Screenshot.objects.all().count()

    context = {'nb_movie': nb_movie, 'nb_quote': nb_quote, 'nb_question': nb_question, 'nb_screenshot': nb_screenshot}
    return render(request, 'quizz/about.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'quizz/contact_success.html')
        else:
            return render(request, 'quizz/contact.html', {'form': form})
    form = ContactForm()
    context = {'form': form}
    return render(request, 'quizz/contact.html', context)


def editor(request):
    context = {}
    movies = Movie.objects.filter(has_quote=1)
    if request.LANGUAGE_CODE == 'fr':
        list_movie = [m.name + f' ({m.year})' for m in movies]
        dict_m = {(m.name + f' ({m.year})'): 'null' for m in movies}
    else:
        list_movie = [m.en_name + f' ({m.year})' for m in movies]
        dict_m = {(m.en_name + f' ({m.year})'): 'null' for m in movies}
    context['list_movie'] = list_movie
    context['dict_m'] = mark_safe(json.dumps(dict_m))
    return render(request, 'quizz/editor.html', context)


def save_preset(request):
    name = request.POST.get('name')
    list_movie_str = json.loads(request.POST.get('list_movie'))
    list_movie = [get_object_or_404(Movie, name=movie_str[:-7], year=int(movie_str[-5:-1])).id for movie_str in
                  list_movie_str]

    list_movie_str = ",".join(list(map(str, list_movie)))

    if 'user_id' not in request.session:
        user_id, user_name = create_user(request)
        time.sleep(0.5)

    preselect = Preselect(name=name, list_movie=list_movie_str, author=request.session['user_id'])
    preselect.save()

    resp = {}
    return JsonResponse(resp)


"""
def exploration(request):
    context = {}
    movies = Movie.objects.filter(has_quote=1)
    list_movie = [m.name + f' ({m.year})' for m in movies]
    context['list_movie'] = list_movie
    return render(request, 'quizz/exploration.html', context)

def __nlp_pipeline(text):

    text = text.lower()
    text = re.sub(r"[,\!\?\%\(\)\/\"]", "", text)
    text = re.sub(r"\&\S*\s", "", text)
    text = re.sub(r"\- ", "", text)
    text = re.sub(r"\n", " ", text)
    
    return text

def get_movie_info(request):
    movie_str = request.GET.get('movie_name')
    movie_name = movie_str[:-7]
    year = int(movie_str[-5:-1])
    movie = get_object_or_404(Movie, name=movie_name, year=year)

    all_quotes = list(Quote.objects.filter(movie_id=movie.id).values_list('quote_text', flat=True))
    quotes = list(random.sample(all_quotes, 10))

    #########################
    # Most significant words
    #########################
    movie_txt = ''.join(all_quotes)
    movie_txt = __nlp_pipeline(movie_txt)

    tokens = word_tokenize(movie_txt)
    words = [word for word in tokens if word.isalpha()]
    words = [w for w in words if not w in STOP_WORDS]
    words = [w for w in words if not w in STOP_WORDS2]

    # Stem / Unstem
    dict_stem = {}
    list_stemmed = []
    stemmer = SnowballStemmer(language='french')
    for w in words:
        stem_w = stemmer.stem(w)
        list_stemmed.append(stem_w)
        if stem_w in dict_stem.keys():
            if w in dict_stem[stem_w].keys():
                dict_stem[stem_w][w] += 1
            else:
                dict_stem[stem_w][w] = 1
        else:
            dict_stem[stem_w] = {w:1}

    # Translate dict (stem to unstem)
    dict_stem_translate = {}
    for w in dict_stem.keys():
        dict_stem_translate[w] = max(dict_stem[w].items(), key=operator.itemgetter(1))[0]

    words = []    
    for w in list_stemmed:
        words.append(dict_stem_translate[w])

    most_freq = Counter(words).most_common(100)

    dict_score = {}
    for w,s in most_freq:
        try:
            freq = DF_FREQ.loc[w]
            dict_score[w] = 100 * (s / freq)
        except KeyError:
            pass
        
    dict_score = dict(sorted(dict_score.items(), key=lambda item: item[1], reverse=True))
    words_sign = list(dict_score.keys())[:20]


    ###############################

    resp = {'name': movie.name, 'year': movie.year, 'image_url': str(movie.image), 'director': movie.director, 'quotes': quotes, 'words_sign': words_sign}
    return JsonResponse(resp)
"""


def home(request):
    context = {}
    return render(request, 'quizz/home.html', context)


def switch_language(request):
    if 'django_language' not in request.COOKIES:
        new_language = 'en'
    elif request.COOKIES['django_language'] == 'en':
        new_language = 'fr'
    elif request.COOKIES['django_language'] == 'fr':
        new_language = 'en'

    json = JsonResponse({'new_language': new_language})
    json.set_cookie('django_language', new_language, max_age=None)
    return json


def switch_language_mobile(request):
    if 'django_language' not in request.COOKIES:
        new_language = 'en'
    elif request.COOKIES['django_language'] == 'en':
        new_language = 'fr'
        request.COOKIES['django_language'] = 'fr'
    elif request.COOKIES['django_language'] == 'fr':
        new_language = 'en'
        request.COOKIES['django_language'] = 'en'
    response = redirect('/')
    response.set_cookie('django_language', new_language, max_age=None)
    return response


def english_home(request):
    new_language = 'en'
    request.COOKIES['django_language'] = 'en'
    response = redirect('/')
    response.set_cookie('django_language', new_language, max_age=None)
    return response


def update_selection(request):
    data = {}
    if request.POST.get('select'):
        genres = Genre.objects.all()

        list_genre_id = []
        for g in genres:
            if request.POST.get(f'genre_{g.id}'):
                list_genre_id.append(g.id)

        list_genre_id_img = []
        for g in genres:
            if request.POST.get(f'genreimg_{g.id}'):
                list_genre_id_img.append(g.id)

        presel_id = int(request.POST.get('presel'))
        year1 = int(request.POST.get('year1'))
        year2 = int(request.POST.get('year2'))
        nb_question = int(request.POST.get('nb_question'))
        popularity = request.POST.get('popularity')
        mode = request.POST.get('mode')
        game_mode = request.POST.get('game_mode')
        game_mode_debrief = request.POST.get('game_mode_debrief')
        country = int(request.POST.get('country')[1:])

        year1_img = int(request.POST.get('year1_img'))
        year2_img = int(request.POST.get('year2_img'))
        nb_question_img = int(request.POST.get('nb_question_img'))
        nsfw_filter = int(request.POST.get('nsfw_filter'))
        popularity_img = request.POST.get('popularity_img')
        country_img = int(request.POST.get('country_img')[1:])

        language = request.LANGUAGE_CODE
        list_movie_sel_real = json.loads(request.POST.get('selected_movies'))
        reset = int(request.POST.get('reset'))

        if game_mode != 'chill':
            game_mode = int(game_mode)

        if game_mode_debrief != 'chill':
            game_mode_debrief = int(game_mode_debrief)

        # Not very clear

        if presel_id == -1:
            if len(list_genre_id) != 0 or country != -1:
                if len(list_genre_id) != 0:
                    list_movie_id_genre = list(
                        MovieGenre.objects.filter(genre_id__in=list_genre_id).values_list('movie_id', flat=True))
                else:
                    list_movie_id_genre = list(Movie.objects.all().order_by('name').values_list('id', flat=True))

                if country != -1:
                    list_movie_id_country = list(
                        MovieCountry.objects.filter(country_id=country).values_list('movie_id', flat=True))
                else:
                    list_movie_id_country = list(Movie.objects.all().order_by('name').values_list('id', flat=True))

                list_movie_id = list(set(list_movie_id_genre).intersection(list_movie_id_country))

                if (year1 != 1900 or year2 != 2025):
                    if language == 'fr':
                        list_movie = Movie.objects.filter(year__gte=year1, year__lte=year2, id__in=list_movie_id,
                                                          has_quote=1).order_by('name')
                    else:
                        list_movie = Movie.objects.filter(year__gte=year1, year__lte=year2, id__in=list_movie_id,
                                                          has_quote_en=1).order_by('name')
                else:
                    if language == 'fr':
                        list_movie = Movie.objects.filter(id__in=list_movie_id, has_quote=1).order_by('name')
                    else:
                        list_movie = Movie.objects.filter(id__in=list_movie_id, has_quote_en=1).order_by('name')
            else:
                if (year1 != 1900 or year2 != 2025):
                    if language == 'fr':
                        list_movie = Movie.objects.filter(year__gte=year1, year__lte=year2, has_quote=1).order_by(
                            'name')
                    else:
                        list_movie = Movie.objects.filter(year__gte=year1, year__lte=year2, has_quote_en=1).order_by(
                            'name')
                else:
                    if language == 'fr':
                        list_movie = Movie.objects.filter(has_quote=1).order_by('name')
                    else:
                        list_movie = Movie.objects.filter(has_quote_en=1).order_by('name')

            if popularity != '':
                l1 = list(list_movie.order_by('-popularity')[:int(popularity)].values_list('id', flat=True))
                list_movie = Movie.objects.filter(id__in=l1).order_by('name')
        else:
            presel = get_object_or_404(Preselect, id=presel_id).list_movie
            presel = presel.split(',')
            list_movie = Movie.objects.filter(id__in=presel).order_by('name')

        # Images
        default_list_img = list(Movie.objects.filter(has_image=1).values_list('id', flat=True))
        dict_param = {'has_image': 1}
        if year1_img != 1900:
            dict_param['year__gte'] = year1_img
        if year2_img != 2025:
            dict_param['year__lte'] = year2_img
        if nsfw_filter == 1:
            dict_param['check_image'] = 1
        if country_img != -1:
            list_movie_id_country_img = list(
                MovieCountry.objects.filter(country_id=country_img).values_list('movie_id', flat=True))
        else:
            list_movie_id_country_img = default_list_img
        if len(list_genre_id) != 0:
            list_movie_id_genre_img = list(
                MovieGenre.objects.filter(genre_id__in=list_genre_id_img).values_list('movie_id', flat=True))
        else:
            list_movie_id_genre_img = default_list_img

        list_movie_id = list(set(list_movie_id_country_img).intersection(list_movie_id_genre_img))
        dict_param['pk__in'] = list_movie_id
        list_movie_img = Movie.objects.filter(**dict_param)

        if popularity_img != '':
            l2 = list(list_movie_img.order_by('-popularity')[:int(popularity_img)].values_list('id', flat=True))
            list_movie_img = Movie.objects.filter(id__in=l2).order_by('name')

        list_movie_sel = list(dict.fromkeys([m.id for m in list_movie]))
        list_movie_sel_img = list(dict.fromkeys([m.id for m in list_movie_img]))

        # Select english movie name if necessary
        if language == 'fr':
            list_movie_sel_name = [m.name + f' ({m.year})' for m in list_movie]
        else:
            list_movie_sel_name = [m.en_name + f' ({m.year})' for m in list_movie]

        if reset:
            list_movie_sel_real = list_movie_sel

        request.session['list_movie_sel'] = list_movie_sel
        request.session['list_movie_sel_name'] = list_movie_sel_name
        request.session['list_movie_sel_real'] = list_movie_sel_real

        request.session['list_genre'] = list_genre_id
        request.session['year1'] = year1
        request.session['year2'] = year2
        request.session['popularity'] = popularity
        request.session['nb_question'] = nb_question
        request.session['mode'] = mode
        request.session['game_mode'] = game_mode
        request.session['game_mode_debrief'] = game_mode_debrief
        request.session['country_selected'] = country
        request.session['presel'] = presel_id

        request.session['list_genre_img'] = list_genre_id_img
        request.session['list_movie_sel_img'] = list_movie_sel_img
        request.session['year1_img'] = year1_img
        request.session['year2_img'] = year2_img
        request.session['nsfw_filter'] = nsfw_filter
        request.session['nb_question_img'] = nb_question_img
        request.session['popularity_img'] = popularity_img
        request.session['country_selected_img'] = country_img

        data['nb_movies_sel'] = len(list_movie_sel_real)
        data['list_movie_sel'] = list_movie_sel
        data['list_movie_sel_name'] = list_movie_sel_name
        data['list_movie_sel_real'] = list_movie_sel_real

        data['list_movie_sel_img'] = list_movie_sel_img
        data['nb_movies_sel_img'] = len(list_movie_sel_img)

        return JsonResponse(data)

    # Do something if it's correct

    # return json or directy html ?


def get_n_random_movies(n=3, list_movie_sel=False, quote=True, image=False):
    if list_movie_sel:
        if quote:
            movies = list(Movie.objects.filter(pk__in=list_movie_sel, has_quote=1))
        elif image:
            movies = list(Movie.objects.filter(pk__in=list_movie_sel, has_image=1))
    else:
        if quote:
            movies = list(Movie.objects.filter(has_quote=1))
        elif image:
            movies = list(Movie.objects.filter(has_image=1))

    return random.sample(movies, n)


def game(request):
    # template_name = 'quizz/game.html'
    context = {}

    if 'question_id' in request.session:
        question = get_object_or_404(Question, pk=request.session['question_id'])
    else:
        # Get 3 random movies
        # num_movies = Movie.objects.all().count()
        # rand_movies = random.sample(range(1, num_movies + 1), 3)
        # sample_movies = Movie.objects.filter(pk__in=rand_movies)

        # If there is a constraint on movies
        if 'list_movie_sel_real' in request.session and len(request.session['list_movie_sel_real']) >= 3:
            sample_movies = get_n_random_movies(3, request.session['list_movie_sel_real'])
        else:
            sample_movies = get_n_random_movies(3)

        # Select a random movie among them
        movie_guessed = random.choice(sample_movies)

        # Select a random quote of this movie
        all_quotes = Quote.objects.filter(movie__pk=movie_guessed.id)
        quote = random.choice(all_quotes)

        # Create a Question object
        question = Question(movie1=Movie.objects.get(pk=sample_movies[0].id),
                            movie2=Movie.objects.get(pk=sample_movies[1].id),
                            movie3=Movie.objects.get(pk=sample_movies[2].id),
                            movie_guessed=Movie.objects.get(pk=movie_guessed.id),
                            quote=quote)
        question.save()

        request.session['question_id'] = question.id

    context['question'] = question
    context['movies'] = [question.movie1, question.movie2, question.movie3]

    return render(request, 'quizz/game.html', context)

# def guess(request):
#     if 'score' not in request.session and 'score_total' not in request.session:
#         request.session['score'] = 0
#         request.session['score_total'] = 0
#
#     if request.GET.get('movie_prop_id') and request.session['question_id']:
#         question = get_object_or_404(Question, pk=request.session['question_id'])
#         movie_prop_id = int(request.GET.get('movie_prop_id', None))
#         data = {'movie_guessed': question.movie_guessed.id}
#
#         request.session['score_total'] += 1
#         if movie_prop_id == question.movie_guessed.id:
#             request.session['score'] += 1
#
#         try:
#             del request.session['question_id']
#         except KeyError:
#             pass
#
#         return JsonResponse(data)
#
#     # Do something if it's correct
#
#     # return json or directy html ?
#
# def reset_score(request):
#     request.session['score'] = 0
#     request.session['score_total'] = 0
#
#     return JsonResponse({})

# def profile(request):
#     context = {}
#     return render(request, 'quizz/profile.html', context)


# class IndexView(TemplateView):
#     template_name = 'quizz/index.html'
#
#
# class TestView(TemplateView):
#     template_name = 'quizz/test.html'
#
#
# class Login(LoginView):
#     template_name = 'quizz/login.html'

# class IndexView(generic.ListView):
#     template_name = 'quizz/index.html'
#     context_object_name = 'latest_games'
#
#     def get_queryset(self):
#         return Game.objects.all()
#
#
# class DetailView(generic.DetailView):
#     model = Game
#     template_name = 'quizz/detail.html'

# def room(request, room_name):
#     return render(request, 'quizz/room_index.html', {
#         'room_name': room_name
#     })
