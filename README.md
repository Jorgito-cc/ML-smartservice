# Machine Learning Backend - Sistema de Recomendación de Técnicos

Sistema de recomendación de técnicos para servicios utilizando Machine Learning (XGBoost Ranker) y Flask.

## 📋 Descripción

Este proyecto implementa un sistema de recomendación que utiliza un modelo de Machine Learning para recomendar técnicos a clientes basándose en múltiples factores como:
- Distancia geográfica
- Calificación promedio
- Historial de servicios
- Precios ofrecidos
- Disponibilidad

## 🛠️ Tecnologías

- **Flask**: Framework web para la API REST
- **XGBoost**: Modelo de Machine Learning para ranking
- **PostgreSQL**: Base de datos
- **Pandas**: Procesamiento de datos
- **Scikit-learn**: Preprocesamiento y escalado
- **Joblib**: Serialización de modelos

## 📦 Instalación

1. **Clonar el repositorio** (si aplica)

2. **Crear entorno virtual**:
```bash
python -m venv venv
```

3. **Activar entorno virtual**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

5. **Configurar base de datos**:
   - Copiar `.env.example` a `.env`
   - Editar `.env` con tus credenciales de PostgreSQL:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=servicios_db
DB_USER=postgres
DB_PASSWORD=tu_password
```

## 🚀 Uso

### 1. Generar Dataset

Primero, necesitas generar el dataset desde la base de datos:

```bash
python build_dataset.py
```

Esto creará el archivo `dataset_tecnicos.csv` con todas las combinaciones solicitud-técnico y sus features.

### 2. Entrenar el Modelo

Una vez generado el dataset, entrena el modelo:

```bash
python train_model.py
```

Esto generará:
- `modelo_recomendacion.pkl`: Modelo entrenado
- `scaler.pkl`: Scaler para normalización de features

### 3. Ejecutar la API

Inicia el servidor Flask:

```bash
python app.py
```

La API estará disponible en `http://localhost:5005`

## 📡 Endpoints

### GET `/`
Información del servicio y endpoints disponibles.

**Respuesta**:
```json
{
  "message": "💡 API ML funcionando.",
  "modelo_cargado": true,
  "scaler_cargado": true,
  "endpoints": {
    "/": "Información del servicio",
    "/recomendar": "POST - Recomendar técnicos para una solicitud",
    "/health": "GET - Estado de salud del servicio"
  }
}
```

### POST `/recomendar`
Recomienda técnicos para una solicitud específica.

**Request Body**:
```json
{
  "id_solicitud": 123
}
```

**Respuesta**:
```json
{
  "id_solicitud": 123,
  "tecnicos_recomendados": [
    {
      "id_tecnico": 1,
      "distancia_km": 5.2,
      "rating_promedio": 4.5,
      "historico_rating": 4.3,
      "cantidad_calificaciones": 15,
      "precio_promedio": 50000,
      "ofertas_totales": 20,
      "servicios_realizados": 45,
      "disponibilidad": 1,
      "score": 0.85
    },
    ...
  ],
  "total": 10
}
```

### GET `/health`
Estado de salud del servicio.

**Respuesta**:
```json
{
  "status": "ok",
  "modelo_cargado": true,
  "scaler_cargado": true,
  "modelo_disponible": true
}
```

## 📁 Estructura del Proyecto

```
machine_backend/
├── app.py                 # Aplicación Flask principal
├── recommender.py         # Lógica de recomendación
├── build_dataset.py       # Generación de dataset desde BD
├── train_model.py         # Entrenamiento del modelo (PRINCIPAL)
├── train.py              # Script alternativo de entrenamiento
├── entrenar_modelo.py    # Script obsoleto (RandomForest)
├── db.py                 # Conexión a base de datos
├── utils.py              # Utilidades (Haversine, etc.)
├── requirements.txt      # Dependencias
├── .env.example          # Ejemplo de configuración
└── README.md            # Este archivo
```

## 🔧 Archivos Generados

Después de ejecutar los scripts, se generarán:
- `dataset_tecnicos.csv`: Dataset para entrenamiento
- `modelo_recomendacion.pkl`: Modelo entrenado
- `scaler.pkl`: Scaler para normalización

## ⚠️ Notas Importantes

1. **Orden de ejecución**: Siempre ejecuta primero `build_dataset.py`, luego `train_model.py`, y finalmente `app.py`.

2. **Base de datos**: Asegúrate de que PostgreSQL esté corriendo y que las tablas necesarias existan:
   - `solicitud_servicio`
   - `tecnico`
   - `tecnico_ubicacion`
   - `calificacion`
   - `oferta_tecnico`
   - `servicio_asignado`

3. **Modelo no encontrado**: Si la API no encuentra el modelo, ejecuta `train_model.py` primero.

4. **Scripts alternativos**: 
   - `train.py` usa un esquema de features diferente
   - `entrenar_modelo.py` está incompleto y no se recomienda usar

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'db'"
- Verifica que `db.py` existe en el directorio raíz

### Error: "dataset_tecnicos.csv no encontrado"
- Ejecuta `python build_dataset.py` primero

### Error: "modelo_recomendacion.pkl no encontrado"
- Ejecuta `python train_model.py` después de generar el dataset

### Error de conexión a base de datos
- Verifica que PostgreSQL esté corriendo
- Revisa las credenciales en `.env`
- Asegúrate de que la base de datos existe

## 📝 Licencia

Este proyecto es parte de un trabajo de grado universitario.

