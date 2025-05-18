"""
Very first-cut ETA logic.

•  Counts how many dishes are *still cooking/queued*.
•  Adds a 10 % per-dish “load factor”.
•  Returns a datetime when we *expect* this new dish to be ready.

Swap the `simple_eta()` call for `ml_eta()` once you have a model.
"""
from datetime import datetime, timedelta
from django.utils import timezone
import math

from ..models import KitchenEvents, MenuItem, OrderItem

LOAD_FACTOR = 0.10           # 10 % extra time per pending dish

def simple_eta(menu_item: MenuItem) -> datetime:
    now = timezone.now()

    pending = KitchenEvents.objects.filter(
        status__in=["queued", "cooking"],
        eta_finish_at__gte=now
    ).count()

    baseline = timedelta(minutes=menu_item.cook_time_min)
    extra    = baseline * LOAD_FACTOR * pending

    return now + baseline + extra


# ── ML placeholder ──────────────────────────────────────────────────────────
#
# (example – comment out until you have a model file saved on disk)
#
# import joblib, numpy as np
#
# _model = joblib.load("models/eta_xgboost.joblib")
# def ml_eta(menu_item: MenuItem) -> datetime:
#     now = timezone.now()
#     X = np.array([[menu_item.cook_time_min, pending, …other features…]])
#     minutes = _model.predict(X)[0]
#     return now + timedelta(minutes=float(minutes))