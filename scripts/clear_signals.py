from soxapp.models import Signal

def run():
    Signal.objects.all().delete()
    print("Deleted all signals")