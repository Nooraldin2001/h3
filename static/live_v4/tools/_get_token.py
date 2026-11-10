import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "h3auctions.settings")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")

import django

django.setup()
from plates.models import LiveBroadcastSession

s = LiveBroadcastSession.objects.order_by("-id").first()
if not s:
    raise SystemExit("no session")
print(s.display_token)
print("id", s.id)
