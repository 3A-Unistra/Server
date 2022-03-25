# User model (ref BDD)
import uuid

from django.db import models


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    password = models.CharField(max_length=256)
    email = models.EmailField()
    piece = models.IntegerField(default=1)
    avatar = models.URLField()

    class Meta:
        db_table = 'users'


class UserFriend(models.Model):
    user = models.ForeignKey(User, related_name='friends_user',
                             on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friends_friend',
                               on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_friends'
        unique_together = ('user', 'friend')


class Game(models.Model):
    name = models.CharField(max_length=64)
    duration = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        db_table = 'games'


class GameUser(models.Model):
    user = models.ForeignKey(User, related_name='users_stats',
                             on_delete=models.CASCADE, null=True)
    game = models.ForeignKey(Game, related_name='users_game',
                             on_delete=models.CASCADE)
    rank = models.IntegerField()
    money = models.IntegerField()
    hotels = models.IntegerField()
    houses = models.IntegerField()
    host = models.BooleanField()
    duration = models.IntegerField()
    bot = models.BooleanField()

    class Meta:
        db_table = 'game_users'
