import os, json, joblib, pandas as pd
from functools import lru_cache
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr.pkl")
FEATS_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr_features.json")

@lru_cache(maxsize=1)
def _load_bundle():
    model = joblib.load(MODEL_PATH)
    with open(FEATS_PATH, "r", encoding="utf-8") as f:
        feats = json.load(f)
    return model, feats

def build_row(signals: dict, calendar: dict, climate: dict) -> pd.DataFrame:
    # Ensamblar exactamente las columnas del modelo
    _, feats = _load_bundle()
    row = {**signals, **calendar, **climate}
    df = pd.DataFrame([row])
    # Alinear y rellenar faltantes
    df = df.reindex(columns=feats, fill_value=0)
    return df

def predict_one(row_df: pd.DataFrame) -> float:
    model, feats = _load_bundle()
    row_df = row_df.reindex(columns=feats, fill_value=0)
    yhat = float(model.predict(row_df)[0])
    return max(yhat, 0.0)  # sin negativos
