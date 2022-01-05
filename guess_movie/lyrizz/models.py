from django.db import models

class Song(models.Model):
    spotify_id = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    raw_name = models.CharField(max_length=200, null=True, blank=True)
    artists = models.CharField(max_length=200, null=True, blank=True)
    raw_artists = models.CharField(max_length=200, null=True, blank=True)
    popularity = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    lang = models.CharField(max_length=200, null=True, blank=True)
    # summary = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='covers_lyrizz', null=True, blank=True)
    has_quote = models.BooleanField(null=True, blank=True)
    has_image = models.BooleanField(default=0, null=True, blank=True)

    def __str__(self):
        return f'{self.artists} - {self.name}'

class Lyrics(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    lyrics_text = models.TextField(null=True, blank=True)
    raw_lyrics_text = models.TextField(null=True, blank=True)
    section = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.lyrics_text


class Game(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    current_q = models.IntegerField(null=True, blank=True)
    nb_q = models.IntegerField(null=True, blank=True)
    host = models.CharField(max_length=200, null=True, blank=True)
    mode = models.CharField(default="start", max_length=200, null=True, blank=True)
    size = models.IntegerField(default=5, null=True, blank=True)
    # "start" ou "random"
    game_mode = models.CharField(default="chill", max_length=200, null=True, blank=True)
    # 'chill' ou int
    game_mode_debrief = models.CharField(default="chill", max_length=200, null=True, blank=True)
    # 'chill' ou int

    def __str__(self):
        return self.name


class Question(models.Model):
    song1 = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='s1')
    song2 = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='s2')
    song3 = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='s3')
    song_guessed = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='sg')
    i_lyrics = models.IntegerField(default=0, null=True, blank=True)
    # ith lyrics of the song_guessed (start)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.song1.id}_{self.song2.id}_{self.song3.id}_{self.i_lyrics}_{self.song_guessed.id}'


class Answer(models.Model):
    user_id = models.CharField(max_length=200, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    song_prop = models.ForeignKey(Song, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user_id}_{self.question}_{self.song_prop}'


class Player(models.Model):
    user_id = models.CharField(max_length=200, null=True, blank=True)
    user_name = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.user_name


class GamePlayer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.game.id}_{self.player.id}'
