from soxapp.models import Game

def run():
    Game.objects.all().delete()
    print("Deleted all games")