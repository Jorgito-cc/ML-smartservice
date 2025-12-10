import pandas as pd
from db import query
from utils import haversine

def construir_dataset():
    """
    Construye el dataset para entrenamiento desde la base de datos.
    Genera todas las combinaciones solicitud-técnico con sus features.
    
    Returns:
        DataFrame con el dataset completo para entrenamiento
    """
    print("🔨 Construyendo dataset desde la base de datos...")
    
    # 1. Cargar solicitudes
    sql_solicitudes = """
        SELECT s.id_solicitud, s.id_cliente, s.id_categoria,
               s.lat AS cliente_lat, s.lon AS cliente_lon,
               s.fecha_publicacion
        FROM solicitud_servicio s
        WHERE s.estado IN ('pendiente','con_ofertas','asignado','completado')
    """
    solicitudes = query(sql_solicitudes)
    
    if solicitudes.empty:
        print("⚠ No hay solicitudes en la base de datos")
        return pd.DataFrame()
    
    print(f"📋 Solicitudes encontradas: {len(solicitudes)}")
    
    # 2. Cargar técnicos con ubicación
    # Intenta con tecnico_ubicacion, si no existe usa valores por defecto
    sql_tecnicos = """
        SELECT t.id_tecnico,
               COALESCE(u.lat, 0) AS tecnico_lat,
               COALESCE(u.lon, 0) AS tecnico_lon,
               t.calificacion_promedio, t.disponibilidad
        FROM tecnico t
        LEFT JOIN tecnico_ubicacion u ON u.id_tecnico = t.id_tecnico
        WHERE t.disponibilidad = TRUE
    """
    
    try:
        tecnicos = query(sql_tecnicos)
    except Exception as e:
        print(f"⚠ Tabla tecnico_ubicacion no encontrada, intentando alternativa...")
        # Alternativa: sin ubicación
        sql_tecnicos = """
            SELECT t.id_tecnico, 0 AS tecnico_lat, 0 AS tecnico_lon,
                   t.calificacion_promedio, t.disponibilidad
            FROM tecnico t
        """
        tecnicos = query(sql_tecnicos)
    
    if tecnicos.empty:
        print("⚠ No hay técnicos disponibles en la base de datos")
        return pd.DataFrame()
    
    print(f"👷 Técnicos disponibles: {len(tecnicos)}")
    
    # 3. Cargar calificaciones históricas
    sql_calificaciones = """
        SELECT id_tecnico, AVG(puntuacion) AS rating_promedio,
               COUNT(*) AS cantidad_calificaciones
        FROM calificacion
        GROUP BY id_tecnico
    """
    calificaciones = query(sql_calificaciones)
    
    # 4. Cargar precios históricos
    sql_precios = """
        SELECT o.id_tecnico, AVG(o.precio) AS precio_promedio,
               COUNT(*) AS ofertas_totales
        FROM oferta_tecnico o
        GROUP BY o.id_tecnico
    """
    precios = query(sql_precios)
    
    # 5. Cargar historial de contratación
    sql_historial = """
        SELECT sa.id_tecnico, COUNT(*) AS servicios_realizados
        FROM servicio_asignado sa
        GROUP BY sa.id_tecnico
    """
    historial = query(sql_historial)
    
    # 6. Cargar asignaciones reales para calcular target
    sql_asignados = """
        SELECT id_solicitud, id_tecnico
        FROM servicio_asignado
    """
    try:
        asignados = query(sql_asignados)
    except Exception as e:
        print(f"⚠ Advertencia: No se pudo cargar asignaciones: {e}")
        asignados = pd.DataFrame(columns=["id_solicitud", "id_tecnico"])
    
    # 7. Construir dataset
    print("🔨 Generando combinaciones solicitud-técnico...")
    dataset = []
    
    for idx, sol in solicitudes.iterrows():
        for _, tec in tecnicos.iterrows():
            distancia = haversine(
                sol["cliente_lat"],
                sol["cliente_lon"],
                tec["tecnico_lat"],
                tec["tecnico_lon"]
            )
            
            # Obtener datos agregados de forma segura
            # Rating histórico
            if not calificaciones.empty:
                rating_historico = calificaciones.loc[
                    calificaciones.id_tecnico == tec.id_tecnico, 
                    "rating_promedio"
                ].fillna(0).values
                rating_historico = rating_historico[0] if len(rating_historico) > 0 else 0
            else:
                rating_historico = 0
            
            # Cantidad de calificaciones
            if not calificaciones.empty:
                cantidad_calif = calificaciones.loc[
                    calificaciones.id_tecnico == tec.id_tecnico, 
                    "cantidad_calificaciones"
                ].fillna(0).values
                cantidad_calif = cantidad_calif[0] if len(cantidad_calif) > 0 else 0
            else:
                cantidad_calif = 0
            
            # Precio promedio
            if not precios.empty:
                precio_prom = precios.loc[
                    precios.id_tecnico == tec.id_tecnico,
                    "precio_promedio"
                ].fillna(0).values
                precio_prom = precio_prom[0] if len(precio_prom) > 0 else 0
            else:
                precio_prom = 0
            
            # Ofertas totales
            if not precios.empty:
                ofertas_tot = precios.loc[
                    precios.id_tecnico == tec.id_tecnico,
                    "ofertas_totales"
                ].fillna(0).values
                ofertas_tot = ofertas_tot[0] if len(ofertas_tot) > 0 else 0
            else:
                ofertas_tot = 0
            
            # Servicios realizados
            if not historial.empty:
                serv_real = historial.loc[
                    historial.id_tecnico == tec.id_tecnico,
                    "servicios_realizados"
                ].fillna(0).values
                serv_real = serv_real[0] if len(serv_real) > 0 else 0
            else:
                serv_real = 0
            
            # Target: 1 si el técnico fue asignado a esta solicitud, 0 si no
            target = 0
            if not asignados.empty:
                matches = asignados[
                    (asignados.id_solicitud == sol.id_solicitud) & 
                    (asignados.id_tecnico == tec.id_tecnico)
                ]
                target = 1 if len(matches) > 0 else 0
            
            dataset.append({
                "id_solicitud": sol["id_solicitud"],
                "id_cliente": sol["id_cliente"],
                "id_tecnico": tec["id_tecnico"],
                "id_categoria": sol["id_categoria"],
                "distancia_km": distancia or 9999,
                "rating_promedio": tec.get("calificacion_promedio", 0) or 0,
                "historico_rating": float(rating_historico),
                "cantidad_calificaciones": int(cantidad_calif),
                "precio_promedio": float(precio_prom),
                "ofertas_totales": int(ofertas_tot),
                "servicios_realizados": int(serv_real),
                "disponibilidad": int(tec.get("disponibilidad", True)),
                "target": target
            })
    
    df = pd.DataFrame(dataset)
    
    if df.empty:
        print("❌ No se pudo generar el dataset")
        return df
    
    print(f"✅ Dataset generado: {len(df)} filas")
    return df

if __name__ == "__main__":
    df = construir_dataset()
    
    if not df.empty:
        df.to_csv("dataset_tecnicos.csv", index=False)
        print(f"💾 Dataset guardado como dataset_tecnicos.csv")
        print(f"📊 Resumen:")
        print(f"   - Total de filas: {len(df)}")
        print(f"   - Solicitudes únicas: {df['id_solicitud'].nunique()}")
        print(f"   - Técnicos únicos: {df['id_tecnico'].nunique()}")
        print(f"   - Técnicos asignados (target=1): {df['target'].sum()}")
    else:
        print("❌ No se pudo generar el dataset")

