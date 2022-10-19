from django.db import models
import pytz

DATETIME_FORMAT = "%I:%M %p"
CT = pytz.timezone("US/Central")

# Create your models here.
class Game(models.Model):
    home_team = models.CharField(max_length=25)
    home_record = models.CharField(max_length=10)
    away_team = models.CharField(max_length=25)
    away_record = models.CharField(max_length=10)
    gametime = models.DateTimeField()
    official_date = models.DateField()
    feed_link = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.away_team} ({self.away_record}) @ {self.home_team} ({self.home_record}) at {self.gametime.astimezone(CT).strftime(DATETIME_FORMAT)} (CT).'

class Signal(models.Model):
    gametime = models.DateTimeField()
    type = models.CharField(max_length=10)

    def __str(self):
        return self.type + " Signal at: " + self.gametime.astimezone(CT).strftime(DATETIME_FORMAT)