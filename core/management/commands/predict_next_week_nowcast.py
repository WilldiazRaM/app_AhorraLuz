import os, json, joblib, pandas as pd
from functools import lru_cache
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr.pkl")
FEATS_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr_features.json")

@lru_cache(maxsize=1)
def _load_bundle():
    """
    Carga el modelo y la lista de features.
    Soporta dos formatos de .pkl:
      A) estimator directo (ej: HistGradientBoostingRegressor)
      B) dict {'model': estimator, 'features': [...]} o similar
    """
    obj = joblib.load(MODEL_PATH)

    model = None
    feats = None

    if isinstance(obj, dict):
        # Casos comunes
        model = obj.get("model", None)
        feats = obj.get("features", None)
        # Si por alguna razón guardaste {'estimator': ...}
        if model is None and "estimator" in obj:
            model = obj["estimator"]
    else:
        # El pickle es un estimator directo
        model = obj

    if model is None:
        raise RuntimeError("El .pkl no contiene un estimator válido (clave 'model' o estimator directo).")

    # Features: intenta desde el pkl primero; si no, desde el JSON externo
    if feats is None:
        with open(FEATS_PATH, "r", encoding="utf-8") as f:
            feats = json.load(f)

    if not isinstance(feats, (list, tuple)) or len(feats) == 0:
        raise RuntimeError("No se pudieron cargar las columnas de features.")

    return model, list(feats)

def build_row(signals: dict, calendar: dict, climate: dict) -> pd.DataFrame:
    _, feats = _load_bundle()
    row = {**signals, **calendar, **climate}
    df = pd.DataFrame([row]).reindex(columns=feats, fill_value=0)
    return df

def predict_one(row_df: pd.DataFrame) -> float:
    model, feats = _load_bundle()
    row_df = row_df.reindex(columns=feats, fill_value=0)
    yhat = float(model.predict(row_df)[0])
    return max(yhat, 0.0)
