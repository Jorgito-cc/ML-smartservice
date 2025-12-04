from math import radians, cos, sin, asin, sqrt
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.
    Retorna la distancia en kilómetros.
    
    Args:
        lat1: Latitud del primer punto
        lon1: Longitud del primer punto
        lat2: Latitud del segundo punto
        lon2: Longitud del segundo punto
    
    Returns:
        Distancia en kilómetros, o None si algún parámetro es None
    """
    if None in (lat1, lon1, lat2, lon2):
        return None
    
    R = 6371  # Radio de la Tierra en kilómetros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c

def haversine_vectorized(lat1, lon1, lat2, lon2):
    """
    Versión vectorizada de Haversine para arrays de NumPy.
    Útil para cálculos en lote sobre grandes datasets.
    
    Args:
        lat1: Array de latitudes del primer punto
        lon1: Array de longitudes del primer punto
        lat2: Array de latitudes del segundo punto
        lon2: Array de longitudes del segundo punto
    
    Returns:
        Array de distancias en kilómetros
    """
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * \
        np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    
    return R * (2 * np.arcsin(np.sqrt(a)))
