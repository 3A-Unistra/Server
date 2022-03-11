# User model (ref BDD)
from django.db.models import Model


class User(Model):
    login = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=64)
    password = models.CharField(max_length=256)
    email = models.EmailField()
    piece = models.IntegerField()
    avatar = models.URLField()


class UserFriend(Model):
    user = models.ForeignKey(User, related_name='friends_user',
                             on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friends_friend',
                               on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'friend')


class Game(Model):
    name = models.CharField(max_length=64)
    duration = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True, blank=True)


class GameUser(Model):
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
