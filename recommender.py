import pandas as pd
import joblib
import numpy as np
import os
from db import query
from utils import haversine

# -----------------------------
# VARIABLES GLOBALES PARA MODELO Y SCALER
# -----------------------------
model = None
scaler = None

def cargar_modelo_recomendacion():
    """
    Carga el modelo y scaler de forma lazy (solo cuando se necesiten).
    Evita errores al importar el módulo si los archivos no existen.
    """
    global model, scaler
    if model is None or scaler is None:
        try:
            if not os.path.exists("modelo_recomendacion.pkl"):
                raise FileNotFoundError("modelo_recomendacion.pkl no encontrado. Ejecuta train_model.py primero.")
            if not os.path.exists("scaler.pkl"):
                raise FileNotFoundError("scaler.pkl no encontrado. Ejecuta train_model.py primero.")
            
            model = joblib.load("modelo_recomendacion.pkl")
            scaler = joblib.load("scaler.pkl")
        except Exception as e:
            raise Exception(f"Error al cargar modelo: {e}")


# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------
def recomendar_tecnicos(id_solicitud):
    """
    Recomienda técnicos para una solicitud específica.
    
    Args:
        id_solicitud: ID de la solicitud de servicio
    
    Returns:
        Lista de diccionarios con técnicos ordenados por score (mejores primero)
    """
    # Cargar modelo si no está cargado
    cargar_modelo_recomendacion()
    
    # 1) Obtener datos de la solicitud
    sql = f"""
        SELECT id_solicitud, id_cliente, id_categoria, lat AS cliente_lat, lon AS cliente_lon
        FROM solicitud_servicio
        WHERE id_solicitud = {id_solicitud}
    """
    sol = query(sql)
    
    if sol.empty:
        return []

    sol = sol.iloc[0]

    # 2) Buscar técnicos disponibles
    sql_tec = """
        SELECT t.id_tecnico, u.lat AS tecnico_lat, u.lon AS tecnico_lon,
               t.calificacion_promedio, t.disponibilidad
        FROM tecnico t
        LEFT JOIN tecnico_ubicacion u ON u.id_tecnico = t.id_tecnico
        WHERE t.disponibilidad = TRUE
    """
    tecnicos = query(sql_tec)

    if tecnicos.empty:
        return []

    # 3) Datos agregados (rating histórico, precios, etc.)
    sql_cal = """
        SELECT id_tecnico, AVG(puntuacion) AS rating_promedio, COUNT(*) AS cantidad 
        FROM calificacion 
        GROUP BY id_tecnico
    """
    sql_pre = """
        SELECT id_tecnico, AVG(precio) AS precio_promedio, COUNT(*) AS ofertas_totales 
        FROM oferta_tecnico 
        GROUP BY id_tecnico
    """
    sql_hist = """
        SELECT id_tecnico, COUNT(*) AS servicios_realizados 
        FROM servicio_asignado 
        GROUP BY id_tecnico
    """

    cal = query(sql_cal)
    pre = query(sql_pre)
    hist = query(sql_hist)

    # 4) Construir dataset temporal
    rows = []
    for _, t in tecnicos.iterrows():
        distancia = haversine(
            sol["cliente_lat"], sol["cliente_lon"],
            t["tecnico_lat"], t["tecnico_lon"]
        )

        # Obtener datos agregados de forma segura (evitar IndexError)
        rating_historico = cal.loc[cal.id_tecnico == t.id_tecnico, "rating_promedio"].fillna(0).values
        rating_historico = rating_historico[0] if len(rating_historico) > 0 else 0
        
        cantidad_calif = cal.loc[cal.id_tecnico == t.id_tecnico, "cantidad"].fillna(0).values
        cantidad_calif = cantidad_calif[0] if len(cantidad_calif) > 0 else 0
        
        precio_prom = pre.loc[pre.id_tecnico == t.id_tecnico, "precio_promedio"].fillna(0).values
        precio_prom = precio_prom[0] if len(precio_prom) > 0 else 0
        
        ofertas_tot = pre.loc[pre.id_tecnico == t.id_tecnico, "ofertas_totales"].fillna(0).values
        ofertas_tot = ofertas_tot[0] if len(ofertas_tot) > 0 else 0
        
        serv_real = hist.loc[hist.id_tecnico == t.id_tecnico, "servicios_realizados"].fillna(0).values
        serv_real = serv_real[0] if len(serv_real) > 0 else 0

        rows.append({
            "id_tecnico": t.id_tecnico,
            "distancia_km": distancia or 9999,
            "rating_promedio": t.calificacion_promedio or 0,
            "historico_rating": float(rating_historico),
            "cantidad_calificaciones": int(cantidad_calif),
            "precio_promedio": float(precio_prom),
            "ofertas_totales": int(ofertas_tot),
            "servicios_realizados": int(serv_real),
            "disponibilidad": int(t.disponibilidad),
        })

    if not rows:
        return []
    
    df = pd.DataFrame(rows)

    # 5) Features
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
        raise ValueError(f"Features faltantes en el dataset: {missing_features}")

    # 6) Escalar y predecir
    X = scaler.transform(df[features])
    df["score"] = model.predict(X)

    # 7) Ordenar DESC → mejores primero
    df = df.sort_values(by="score", ascending=False)

    return df.to_dict(orient="records")
