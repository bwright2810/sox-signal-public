from soxapp.models import Signal
from datetime import datetime

def run():
  now = datetime.now()
  print(Signal.objects.filter(gametime__year=now.year, gametime__month=now.month, gametime__day=now.day))