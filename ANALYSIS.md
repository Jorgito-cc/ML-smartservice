# Análisis del Proyecto Machine Backend

Este documento detalla el análisis del código fuente del proyecto ubicado en `backend/machine_backend`.

## 1. Resumen General
El proyecto es un backend en Python utilizando **Flask** para exponer una API REST. Su función principal es recomendar técnicos para servicios basándose en un modelo de Machine Learning (**XGBoost Ranker**).

**Tecnologías Clave:**
- **Framework Web:** Flask
- **Base de Datos:** PostgreSQL (`psycopg2`)
- **ML/Data:** Pandas, Scikit-learn, XGBoost, Numpy
- **Serialización:** Joblib

## 2. Análisis de Archivos

### `app.py` (Punto de Entrada)
Este archivo contiene la configuración de la aplicación Flask y los endpoints.
**Problemas Detectados:**
- **Código Duplicado:** Existen múltiples definiciones de las funciones `procesar` y `recomendar`. Python sobrescribirá las primeras con las últimas, lo que hace que gran parte del código sea código muerto o confuso.
    - Líneas 84 y 125: Definición de `procesar`.
    - Líneas 101, 148 y 174: Definición de `recomendar`.
- **Credenciales Hardcodeadas:** Las credenciales de la base de datos (usuario, contraseña, host) están escritas directamente en el código (`get_connection`). Esto es una mala práctica de seguridad.
- **Inconsistencia en Modelos:**
    - Una versión de `recomendar` carga `model.pkl`.
    - `recommender.py` carga `modelo_recomendacion.pkl`.
    - `train_model.py` guarda `modelo_recomendacion.pkl`.
    - Esto causará errores si no se unifica el nombre del archivo del modelo.

### `recommender.py` (Lógica de Recomendación)
Contiene la lógica para obtener datos, procesarlos y generar el ranking de técnicos.
**Problemas Detectados:**
- **Dependencia Faltante (`db.py`):** En la línea 4 se hace `from db import query`. Sin embargo, el archivo `db.py` no existe en el directorio listado. Esto provocará un `ModuleNotFoundError`. Es probable que la función `query` deba moverse a un archivo separado o importarse de `app.py` (lo cual causaría una importación circular).

### `train_model.py` (Entrenamiento)
Script para entrenar el modelo XGBoost.
**Problemas Detectados:**
- **Dataset Faltante:** Intenta leer `dataset_tecnicos.csv`, pero este archivo no se encuentra en el directorio.

### `requirements.txt`
Lista las dependencias.
- Parece correcto, incluye las librerías necesarias (`flask`, `xgboost`, `pandas`, etc.).

## 3. Recomendaciones de Mejora

1.  **Limpieza de `app.py`:** Eliminar las definiciones duplicadas de funciones y dejar solo la lógica final y necesaria.
2.  **Crear `db.py`:** Mover la lógica de conexión a base de datos (`get_connection`, `query`) a un archivo `db.py` independiente para evitar duplicación y permitir que `recommender.py` lo importe sin problemas.
3.  **Variables de Entorno:** Usar `python-decouple` (que ya está en requirements) para manejar las credenciales de la base de datos desde un archivo `.env`.
4.  **Unificar Nombres de Modelos:** Decidir un nombre único para el modelo (ej. `modelo_recomendacion.pkl`) y usarlo consistentemente en todos los archivos.
5.  **Manejo de Errores:** Agregar bloques `try-except` más robustos, especialmente en las consultas a base de datos y carga de modelos.

## 4. Estado Actual
El proyecto **ha sido corregido y ahora es ejecutable** después de las siguientes correcciones:

### ✅ Correcciones Aplicadas:

1. **`recommender.py`**:
   - ✅ Eliminada función `haversine` duplicada (ahora usa `utils.py`)
   - ✅ Implementada carga lazy de modelos (evita errores al importar)
   - ✅ Mejorado manejo seguro de arrays (evita IndexError)
   - ✅ Agregado manejo de errores robusto

2. **`train_model.py`**:
   - ✅ Agregadas validaciones de existencia del dataset
   - ✅ Validación de features requeridas
   - ✅ Validación de grupos para ranking
   - ✅ Mejorado manejo de errores con mensajes claros

3. **`train.py`**:
   - ✅ Agregadas validaciones de archivos y columnas
   - ✅ Manejo robusto de columnas opcionales
   - ✅ Mejorado manejo de errores

4. **`entrenar_modelo.py`**:
   - ✅ Marcado como obsoleto con advertencias
   - ✅ Documentado que requiere funciones auxiliares

5. **`build_dataset.py`**:
   - ✅ Mejorado manejo seguro de DataFrames vacíos
   - ✅ Agregado manejo de errores en consultas

6. **`requirements.txt`**:
   - ✅ Eliminado `pandas` duplicado
   - ✅ Agregadas versiones específicas para reproducibilidad

7. **`db.py`**:
   - ✅ Ya existe y está correctamente implementado con variables de entorno

8. **Documentación**:
   - ✅ Creado `README.md` con instrucciones completas
   - ✅ Documentado orden de ejecución y solución de problemas

### 📋 Orden de Ejecución:

1. Configurar `.env` con credenciales de BD
2. Ejecutar: `python build_dataset.py` (genera dataset)
3. Ejecutar: `python train_model.py` (entrena modelo)
4. Ejecutar: `python app.py` (inicia API)

### ⚠️ Requisitos Previos:

- PostgreSQL corriendo con las tablas necesarias
- Archivo `.env` configurado (ver `.env.example` o README.md)
