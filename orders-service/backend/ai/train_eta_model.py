import pandas as pd, joblib, datetime as dt
from cryptography.hazmat.backends.openssl import backend
from django.db.models import F, DurationField, ExpressionWrapper
from ..models import KitchenEvent

def run():
    events = (
        KitchenEvent.objects
        .filter(finished_at__isnull=False,
                finished_at__gte=dt.date.today()-dt.timedelta(days=30))
        .annotate(
            cook_sec = ExpressionWrapper(
                F("finished_at") - F("started_at"),
                output_field=DurationField())
        )
        .values("order_item__menu_item", "cook_sec", "started_at")
    )

    if not events:
        return  # nothing to train yet

    df = pd.DataFrame.from_records(events)
    df["cook_min"] = df["cook_sec"].dt.total_seconds() / 60
    df["hour"]     = df["started_at"].dt.hour
    df["weekday"]  = df["started_at"].dt.weekday

    from sklearn.ensemble import GradientBoostingRegressor
    X = pd.get_dummies(df[["order_item__menu_item", "hour", "weekday"]],
                       columns=["order_item__menu_item", "weekday"])
    y = df["cook_min"]

    model = GradientBoostingRegressor().fit(X, y)
    joblib.dump((model, X.columns.tolist()), "/app/eta_model.joblib")