"""
Script alternativo para entrenar modelo de ranking.
NOTA: Este script usa un esquema de features diferente a train_model.py.
Se recomienda usar train_model.py que es el script principal.
"""
import pandas as pd
import numpy as np
from xgboost import XGBRanker
import joblib
import os
import sys
from utils import haversine

def cargar_datos():
    """Carga y preprocesa el dataset"""
    if not os.path.exists("dataset_tecnicos.csv"):
        raise FileNotFoundError("dataset_tecnicos.csv no encontrado. Ejecuta build_dataset.py primero")
    
    df = pd.read_csv("dataset_tecnicos.csv")
    
    if df.empty:
        raise ValueError("El dataset está vacío")
    
    # Si el dataset ya tiene distancia_km, usarlo directamente
    if "distancia_km" in df.columns:
        df["distancia"] = df["distancia_km"]
    elif all(col in df.columns for col in ["lat_cliente", "lon_cliente", "lat_tecnico", "lon_tecnico"]):
        # Calcular distancia si tenemos coordenadas
        df["distancia"] = df.apply(lambda row:
            haversine(
                row["lat_cliente"], row["lon_cliente"],
                row["lat_tecnico"], row["lon_tecnico"]
            ), axis=1
        )
    else:
        print("⚠ Advertencia: No se encontraron coordenadas para calcular distancia")
        df["distancia"] = 0

    # Manejar columnas opcionales
    if "calificacion" in df.columns:
        df["calificacion"] = df["calificacion"].fillna(3)
    elif "rating_promedio" in df.columns:
        df["calificacion"] = df["rating_promedio"].fillna(3)
    else:
        df["calificacion"] = 3
    
    if "tiempo_respuesta" in df.columns:
        df["tiempo_respuesta"] = df["tiempo_respuesta"].fillna(120)
    else:
        df["tiempo_respuesta"] = 120
    
    if "precio" in df.columns:
        df["precio"] = df["precio"].fillna(df["precio"].median() if len(df) > 0 else 0)
    elif "precio_promedio" in df.columns:
        df["precio"] = df["precio_promedio"].fillna(0)
    else:
        df["precio"] = 0
    
    df = df.fillna(0)
    return df

def entrenar_modelo():
    """Entrena un modelo XGBRanker con features alternativas"""
    try:
        df = cargar_datos()
    except Exception as e:
        print(f"❌ Error al cargar datos: {e}")
        sys.exit(1)

    features = ["distancia", "precio", "calificacion", "tiempo_respuesta"]
    
    # Verificar que las features existan
    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f"❌ Features faltantes: {missing}")
        print(f"   Columnas disponibles: {list(df.columns)}")
        sys.exit(1)
    
    X = df[features].values
    
    # Buscar target
    if "contratado" in df.columns:
        y = df["contratado"].values
    elif "target" in df.columns:
        print("⚠ Usando 'target' en lugar de 'contratado'")
        y = df["target"].values
    else:
        print("❌ No se encontró columna 'contratado' ni 'target'")
        sys.exit(1)

    if "id_solicitud" not in df.columns:
        print("❌ Error: 'id_solicitud' no encontrado en el dataset")
        sys.exit(1)

    group = df.groupby("id_solicitud").size().tolist()
    
    if not group:
        print("❌ No se pueden crear grupos para ranking")
        sys.exit(1)

    ranker = XGBRanker(
        objective='rank:pairwise',
        learning_rate=0.1,
        n_estimators=200,
        max_depth=6,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        verbosity=1
    )

    try:
        ranker.fit(X, y, group=group)
        joblib.dump(ranker, "modelo_ranking.pkl")
        print("✅ Modelo entrenado y guardado como modelo_ranking.pkl")
    except Exception as e:
        print(f"❌ Error al entrenar modelo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    entrenar_modelo()
