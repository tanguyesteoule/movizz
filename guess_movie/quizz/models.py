from django.db import models


class Movie(models.Model):
    imdb_id = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    original_name = models.CharField(max_length=200, null=True, blank=True)
    en_name = models.CharField(max_length=200, null=True, blank=True) # English name
    director = models.CharField(max_length=200, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='covers', null=True, blank=True)
    has_quote = models.BooleanField(null=True, blank=True)
    has_image = models.BooleanField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name


class Contact(models.Model):
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return self.subject


class Quote(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    quote_text = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.quote_text


class Screenshot(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='screenshot', null=True, blank=True)
    num_img = models.IntegerField(null=True, blank=True)
    sfw = models.BooleanField(default=1, null=True, blank=True)



class Game(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    current_q = models.IntegerField(null=True, blank=True)
    nb_q = models.IntegerField(null=True, blank=True)
    host = models.CharField(max_length=200, null=True, blank=True)
    mode = models.CharField(default="quote", max_length=200, null=True, blank=True)
    # "quote" ou "image"
    game_mode = models.CharField(max_length=200, null=True, blank=True)
    # 'chill' ou int
    game_mode_debrief = models.CharField(max_length=200, null=True, blank=True)

    # 'chill' ou int

    def __str__(self):
        return self.name


class Question(models.Model):
    movie1 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='m1')
    movie2 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='m2')
    movie3 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='m3')
    movie_guessed = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='mg')
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.movie1.id}_{self.movie2.id}_{self.movie3.id}_{self.quote.id}_{self.movie_guessed.id}'


class QuestionImage(models.Model):
    movie1 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='mi1')
    movie2 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='mi2')
    movie3 = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='mi3')
    movie_guessed = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='mig')
    list_image_id = models.TextField(null=True, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.game}_{self.movie_guessed.id}'


class Answer(models.Model):
    user_id = models.CharField(max_length=200, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    movie_prop = models.ForeignKey(Movie, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user_id}_{self.question}_{self.movie_prop}'


class AnswerImage(models.Model):
    user_id = models.CharField(max_length=200, null=True, blank=True)
    questionimage = models.ForeignKey(QuestionImage, on_delete=models.CASCADE)
    movie_prop = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.user_id}_{self.questionimage}_{self.movie_prop}'


class Genre(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    user_id = models.CharField(max_length=200, null=True, blank=True)
    user_name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.user_name


class Preselect(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    list_movie = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.movie.id}_{self.genre.id}'


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.game.id}_{self.player.id}'


class MovieCountry(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.movie.id}_{self.country.id}'
