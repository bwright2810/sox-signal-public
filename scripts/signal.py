from twilio.rest import Client
import os
from datetime import datetime, timedelta
from soxapp.models import Game, Signal
import pytz
from dateutil import parser
import requests
import json
import pytz

CT = pytz.timezone("US/Central")
SECONDS_IN_DAY = 24 * 60 * 60
NOTIFY_MINUTES = 20
START_TYPE = "Game Start"
END_TYPE = "Game End"
BASE_API = "http://statsapi.mlb.com"

def val(arr, key):
    for arg in arr:
        if key in arg:
            return arg.split('=')[1]
    return os.getenv(key)

def run(*args):
    sid = val(args, 'TWILIO_SID')
    token = val(args, 'TWILIO_TOKEN')
    from_phone = val(args, 'FROM_PHONE')
    to_phone = val(args, 'TO_PHONE')
    runtime_string = val(args, 'RUNTIME')
    runtime = parser.parse(runtime_string.replace('_', ' ')) if runtime_string else pytz.UTC.localize(datetime.now())
    runtime_ct = runtime.astimezone(CT)
    notify_minutes = val(args, 'NOTIFY_MINUTES') or NOTIFY_MINUTES

    end_window = runtime + timedelta(minutes=notify_minutes)

    games = Game.objects.filter(official_date__year=runtime_ct.year, official_date__month=runtime_ct.month, official_date__day=runtime_ct.day)

    if len(games) > 0:
        for game in games:
            if runtime <= game.gametime <= end_window:
                signals = Signal.objects.filter(gametime=game.gametime).filter(type=START_TYPE)
                if len(signals) > 0:
                    print("Already sent text for this game. Skipping.")
                else:
                    time_til_game = game.gametime - runtime
                    minutes_til = divmod(time_til_game.days * SECONDS_IN_DAY + time_til_game.seconds, 60)[0]
                    
                    client = Client(sid, token) 
                    client.messages.create(from_=from_phone, to=to_phone, body=f'SOX game in {minutes_til} minutes. {game}')
                    Signal.objects.create(gametime=game.gametime, type=START_TYPE)
                    print("Sent text for upcoming game and created Signal in DB.")
            elif not runtime > game.gametime:
                print(f'There is a game today, but it\'s not currently within {notify_minutes} minutes. Skipping game start text.')

            if runtime > game.gametime:
                # TODO games that go over midnight would be on previous day
                end_signals = Signal.objects.filter(gametime=game.gametime).filter(type=END_TYPE)
                if len(end_signals) > 0:
                    print("Already sent game end text for this game. Skipping game end text.")
                else:
                    url = BASE_API + game.feed_link
                    r = requests.get(url)
                    feed = json.loads(r.text)
                    status = feed["gameData"]["status"]["abstractGameState"]
                    if status == "Final":
                        home_score = feed["liveData"]["linescore"]["teams"]["home"]["runs"]
                        away_score = feed["liveData"]["linescore"]["teams"]["away"]["runs"]

                        winner = [game.home_team, home_score] if home_score > away_score else [game.away_team, away_score]
                        loser = [game.home_team, home_score] if home_score < away_score else [game.away_team, away_score]

                        client = Client(sid, token) 
                        client.messages.create(from_=from_phone, to=to_phone, body=f'SOX game over. The {winner[0]} defeated the {loser[0]}, {winner[1]} to {loser[1]}.')
                        Signal.objects.create(gametime=game.gametime, type=END_TYPE)
                        print("Sent text for finished game and created Signal in DB.")
                    else:
                        print("Game is not over yet. Skipping game end text.")



    