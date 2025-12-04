import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import ndcg_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRanker
import joblib
import os
import sys

# ------------------------------
# 1. Verificar y cargar dataset
# ------------------------------
if not os.path.exists("dataset_tecnicos.csv"):
    print("❌ Error: dataset_tecnicos.csv no encontrado")
    print("   Ejecuta primero: python build_dataset.py")
    sys.exit(1)

df = pd.read_csv("dataset_tecnicos.csv")

print("📌 Dataset cargado:", df.shape)

if df.empty:
    print("❌ El dataset está vacío")
    sys.exit(1)

# ------------------------------
# 2. Limpieza
# ------------------------------
df.fillna(0, inplace=True)

# ------------------------------
# 3. Definir FEATURES
# ------------------------------
features = [
    "distancia_km",
    "rating_promedio",
    "historico_rating",
    "cantidad_calificaciones",
    "precio_promedio",
    "ofertas_totales",
    "servicios_realizados",
    "disponibilidad",
]

# Verificar que todas las features existan
missing_features = [f for f in features if f not in df.columns]
if missing_features:
    print(f"❌ Features faltantes en el dataset: {missing_features}")
    print(f"   Columnas disponibles: {list(df.columns)}")
    sys.exit(1)

X = df[features]

# ------------------------------
# 4. Definir TARGET (ranking)
# ------------------------------
# IMPORTANTE: aquí el modelo aprende a priorizar técnicos seleccionados
if "target" not in df.columns:
    print("⚠ Advertencia: no existe 'target' en el dataset.")
    print("   Se asignará dummy (todos 0). Debes reemplazar con datos reales después.")
    df["target"] = 0

y = df["target"]

# ------------------------------
# 5. Agrupar por solicitud para ranking
# ------------------------------
if "id_solicitud" not in df.columns:
    print("❌ Error: 'id_solicitud' no encontrado en el dataset")
    sys.exit(1)

groups = df.groupby("id_solicitud").size().to_list()

if len(groups) == 0:
    print("❌ Error: No se pueden crear grupos para ranking")
    sys.exit(1)

# ------------------------------
# 6. Escalado (MEJOR rendimiento)
# ------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ------------------------------
# 7. Entrenamiento del modelo
# ------------------------------
print("🚀 Entrenando modelo XGBoost Ranker...")

model = XGBRanker(
    objective="rank:pairwise",
    learning_rate=0.1,
    n_estimators=200,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=1
)

try:
    model.fit(
        X_scaled,
        y,
        group=groups,
    )
    print("✅ Modelo entrenado correctamente.")
except Exception as e:
    print(f"❌ Error al entrenar modelo: {e}")
    sys.exit(1)

# ------------------------------
# 8. Evaluación (NDCG)
# ------------------------------
try:
    predictions = model.predict(X_scaled)
    ndcg = ndcg_score([y], predictions.reshape(1, -1))
    print(f"📊 NDCG Score: {ndcg:.4f}")
except Exception as e:
    print(f"⚠ No se pudo calcular NDCG: {e}")

# ------------------------------
# 9. Guardar MODELO + SCALER
# ------------------------------
try:
    joblib.dump(model, "modelo_recomendacion.pkl")
    joblib.dump(scaler, "scaler.pkl")
    print("💾 Modelo guardado como modelo_recomendacion.pkl")
    print("💾 Scaler guardado como scaler.pkl")
except Exception as e:
    print(f"❌ Error al guardar modelo: {e}")
    sys.exit(1)
