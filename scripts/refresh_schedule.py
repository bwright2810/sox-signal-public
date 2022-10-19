import requests
import json
from dateutil import parser
from datetime import datetime
from soxapp.models import Game
from django.db import transaction
from twilio.rest import Client
import os
import pytz
import functools
import pytz

CT = pytz.timezone("US/Central")
SCHEDULE_URL = 'http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&startDate=DATE_PARAM&endDate=DATE_PARAM'
DATE_FORMAT = "%Y-%m-%d"

def val(arr, key):
    for x in arr:
        if key in x:
            split = x.split('=')
            return split[1]
    return os.getenv(key)

def home(game, side="home"):
    return game["teams"][f'{side}']["team"]["name"]

def away(game):
    return home(game, "away")

def run(*args):
    runtime_string = val(args, 'MORN_RUNTIME')
    runtime_ct = parser.parse(runtime_string.replace('_', ' ')) if runtime_string else datetime.now().astimezone(CT)
    date_param = runtime_ct.strftime(DATE_FORMAT)
    modified_url = SCHEDULE_URL.replace('DATE_PARAM', date_param)

    r = requests.get(modified_url)
    games_resp = json.loads(r.text)
    games_list = games_resp["dates"][0]["games"]
    sox_games = [g for g in games_list if home(g) == "Chicago White Sox" or away(g) == "Chicago White Sox"]

    if sox_games:
        for game in sox_games: # in case of double header
            game = sox_games[0]

            with transaction.atomic():
                gametime = parser.parse(game["gameDate"])
                Game.objects.filter(gametime=gametime).delete()

                Game.objects.create(
                    home_team=home(game),
                    home_record= f'{game["teams"]["home"]["leagueRecord"]["wins"]}-{game["teams"]["home"]["leagueRecord"]["losses"]}',
                    away_team=away(game),
                    away_record= f'{game["teams"]["away"]["leagueRecord"]["wins"]}-{game["teams"]["away"]["leagueRecord"]["losses"]}',
                    gametime=gametime,
                    official_date=game["officialDate"],
                    feed_link=game["link"]
                )
        print("Updated schedule")
    else:
        print("No SOX games found")

    sid = val(args, 'TWILIO_SID')
    token = val(args, 'TWILIO_TOKEN')
    from_phone = val(args, 'FROM_PHONE')
    to_phone = val(args, 'TO_PHONE')

    games = Game.objects.filter(official_date__year=runtime_ct.year, official_date__month=runtime_ct.month, official_date__day=runtime_ct.day)

    if len(games) > 0:
          game_desc = functools.reduce(lambda g1, g2: str(g1) + ' ' + str(g2), games)
          client = Client(sid, token) 
          client.messages.create(from_=from_phone, to=to_phone, body=f'SOX game today. {game_desc}')
          print("Sent text for Sox game today.")
    else:
      print("No Sox game today.")