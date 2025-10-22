import os, json, joblib, pandas as pd
from functools import lru_cache
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr.pkl")
FEATS_PATH = os.path.join(settings.BASE_DIR, "core", "ml", "modelo_nowcast_hgbr_features.json")

def _has_predict(x) -> bool:
    return hasattr(x, "predict") and callable(getattr(x, "predict", None))

def _find_estimator(obj, depth=0):
    """Busca recursivamente un objeto con .predict dentro de dicts/listas/tuplas."""
    indent = "  " * depth
    print(f"{indent}[_find_estimator] depth={depth}, type={type(obj)}")

    # Caso 1: ya es estimator
    if _has_predict(obj):
        print(f"{indent}✅ estimator encontrado: {type(obj)}")
        return obj

    # Caso 2: dict -> prueba claves típicas y luego recursivo
    if isinstance(obj, dict):
        keys = list(obj.keys())
        print(f"{indent}dict keys={keys[:10]}")
        for k in ["model", "estimator", "sk_model", "clf", "regressor", "best_estimator_", "pipeline"]:
            if k in obj and _has_predict(obj[k]):
                print(f"{indent}✅ estimator en clave '{k}': {type(obj[k])}")
                return obj[k]
        # buscar profundo
        for k, v in obj.items():
            print(f"{indent}→ entrar a clave '{k}'")
            est = _find_estimator(v, depth + 1)
            if est is not None:
                return est
        return None

    # Caso 3: lista/tupla -> recorrer elementos
    if isinstance(obj, (list, tuple)):
        print(f"{indent}list/tuple len={len(obj)}")
        for i, v in enumerate(obj[:20]):  # limitar spam
            print(f"{indent}→ entrar a idx {i}")
            est = _find_estimator(v, depth + 1)
            if est is not None:
                return est
        return None

    # Caso 4: otros tipos
    return None

@lru_cache(maxsize=1)
def _load_bundle():
    """Carga el .pkl (robusto) + features."""
    print(f"[ml_nowcast] Cargando modelo: {MODEL_PATH}")
    obj = joblib.load(MODEL_PATH)
    print(f"[ml_nowcast] tipo raíz del pickle: {type(obj)}")

    model = _find_estimator(obj)
    if model is None:
        keys_hint = obj.keys() if isinstance(obj, dict) else type(obj).__name__
        raise RuntimeError(f"[ml_nowcast] ❌ No se encontró estimator (.predict). Pistas: {keys_hint}")

    # Features: intenta sacarlas del pickle si estuvieran guardadas; si no, del JSON
    feats = None
    if isinstance(obj, dict):
        for k in ["features", "feature_names", "columns"]:
            if k in obj and isinstance(obj[k], (list, tuple)):
                feats = list(obj[k])
                print(f"[ml_nowcast] ✅ features encontradas en pkl: n={len(feats)}")
                break

    if feats is None:
        print(f"[ml_nowcast] Leyendo features desde JSON: {FEATS_PATH}")
        with open(FEATS_PATH, "r", encoding="utf-8") as f:
            feats = json.load(f)

    if not isinstance(feats, (list, tuple)) or len(feats) == 0:
        raise RuntimeError("[ml_nowcast] ❌ No se pudieron cargar features (lista vacía).")

    print(f"[ml_nowcast] ✅ modelo listo ({type(model)}), features={len(feats)}")
    return model, list(feats)

def build_row(signals: dict, calendar: dict, climate: dict) -> pd.DataFrame:
    _, feats = _load_bundle()
    row = {**signals, **calendar, **climate}
    print(f"[build_row] keys entrada={list(row.keys())}")
    df = pd.DataFrame([row]).reindex(columns=feats, fill_value=0)
    print(f"[build_row] df.shape={df.shape}, cols={list(df.columns)}")
    return df

def predict_one(row_df: pd.DataFrame) -> float:
    model, feats = _load_bundle()
    row_df = row_df.reindex(columns=feats, fill_value=0)
    print(f"[predict_one] model={type(model)}, df.shape={row_df.shape}")
    try:
        yhat = float(model.predict(row_df)[0])
        print(f"[predict_one] ✅ yhat={yhat:.6f}")
    except Exception as e:
        print(f"[predict_one] ❌ error en predict(): {e}")
        raise
    return max(yhat, 0.0)
