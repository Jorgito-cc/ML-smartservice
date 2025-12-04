import pandas as pd
import psycopg2
from decouple import config

def get_connection():
    """
    Obtiene conexión a PostgreSQL usando variables de entorno.
    Las credenciales se cargan desde el archivo .env
    """
    return psycopg2.connect(
        host=config("DB_HOST", default="localhost"),
        port=config("DB_PORT", default="5432"),
        database=config("DB_NAME", default="servicios_db"),
        user=config("DB_USER", default="postgres"),
        password=config("DB_PASSWORD", default="123456")
    )

def query(sql):
    """
    Ejecuta una consulta SQL y retorna un DataFrame de pandas.
    
    Args:
        sql: Consulta SQL a ejecutar
    
    Returns:
        DataFrame con los resultados de la consulta
    """
    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn)
        return df
    finally:
        conn.close()

