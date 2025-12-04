# 📚 Guía Completa: Sistema de Recomendación ML

## 🎯 ¿Cómo Funciona el Machine Learning?

### 1. **Tipo de Modelo: XGBoost Ranker**

Este sistema usa **XGBoost Ranker**, que es un modelo de **Learning to Rank** (aprender a ordenar). 

**¿Qué significa esto?**
- No predice un valor exacto (como precio o cantidad)
- **Predice un SCORE (puntuación)** que indica qué tan bueno es un técnico para una solicitud
- Ordena los técnicos de **mejor a peor** según el score

### 2. **Features (Características) que Aprende el Modelo**

El modelo analiza **8 características** de cada técnico:

| Feature | Descripción | ¿Qué significa? |
|---------|-------------|-----------------|
| `distancia_km` | Distancia entre cliente y técnico | Menor = Mejor (técnico más cercano) |
| `rating_promedio` | Calificación promedio del técnico | Mayor = Mejor (técnico más calificado) |
| `historico_rating` | Rating histórico de calificaciones | Mayor = Mejor (historial confiable) |
| `cantidad_calificaciones` | Número de calificaciones recibidas | Mayor = Mejor (más experiencia validada) |
| `precio_promedio` | Precio promedio de ofertas | Menor = Mejor (más económico) |
| `ofertas_totales` | Total de ofertas realizadas | Mayor = Mejor (más activo) |
| `servicios_realizados` | Servicios completados | Mayor = Mejor (más experiencia) |
| `disponibilidad` | Si está disponible (1) o no (0) | 1 = Mejor (disponible) |

### 3. **¿Cómo Aprende el Modelo?**

1. **Entrenamiento** (`train_model.py`):
   - Lee el dataset con todas las combinaciones solicitud-técnico
   - El `target` indica si un técnico fue **realmente seleccionado** (1) o no (0)
   - Aprende patrones: "Los técnicos seleccionados tenían estas características..."
   - Guarda el modelo entrenado

2. **Predicción** (`recommender.py`):
   - Toma una solicitud nueva
   - Calcula las 8 features para cada técnico disponible
   - El modelo predice un **score** para cada técnico
   - Ordena de mayor a menor score

---

## 🔄 Flujo Completo del Sistema

### **FASE 1: Preparación (Una sola vez)**

```
1. build_dataset.py
   ↓
   Consulta PostgreSQL
   ↓
   Genera dataset_tecnicos.csv
   (Todas las combinaciones solicitud-técnico con sus features)
```

**¿Qué hace?**
- Consulta todas las solicitudes de la BD
- Consulta todos los técnicos disponibles
- Para cada combinación solicitud-técnico:
  - Calcula distancia (Haversine)
  - Obtiene calificaciones históricas
  - Obtiene precios promedios
  - Obtiene servicios realizados
  - Marca si fue seleccionado (target = 1) o no (target = 0)

**Resultado:** `dataset_tecnicos.csv` con miles de filas

---

### **FASE 2: Entrenamiento (Una sola vez, o cuando actualices datos)**

```
2. train_model.py
   ↓
   Lee dataset_tecnicos.csv
   ↓
   Entrena XGBoost Ranker
   ↓
   Guarda modelo_recomendacion.pkl + scaler.pkl
```

**¿Qué hace?**
- Lee el dataset
- Separa las 8 features (X) y el target (y)
- Agrupa por solicitud (para ranking)
- Normaliza las features (StandardScaler)
- Entrena el modelo XGBoost
- Guarda el modelo y el scaler

**Resultado:** Modelo entrenado listo para usar

---

### **FASE 3: API en Tiempo Real (Cada vez que necesites recomendaciones)**

```
3. app.py (Flask API)
   ↓
   Recibe: {"id_solicitud": 123}
   ↓
   Llama a recommender.py
   ↓
   Retorna: Lista de técnicos ordenados por score
```

**Proceso detallado:**

1. **Cliente envía solicitud** → `POST /recomendar` con `{"id_solicitud": 123}`

2. **API busca la solicitud en BD:**
   ```sql
   SELECT id_solicitud, id_cliente, id_categoria, lat, lon
   FROM solicitud_servicio
   WHERE id_solicitud = 123
   ```

3. **API busca técnicos disponibles:**
   ```sql
   SELECT t.id_tecnico, u.lat, u.lon, t.calificacion_promedio, t.disponibilidad
   FROM tecnico t
   LEFT JOIN tecnico_ubicacion u ON u.id_tecnico = t.id_tecnico
   WHERE t.disponibilidad = TRUE
   ```

4. **API obtiene datos históricos:**
   - Calificaciones promedio por técnico
   - Precios promedio por técnico
   - Servicios realizados por técnico

5. **API calcula features para cada técnico:**
   - Distancia (Haversine)
   - Rating promedio
   - Rating histórico
   - Cantidad de calificaciones
   - Precio promedio
   - Ofertas totales
   - Servicios realizados
   - Disponibilidad

6. **API normaliza features** (usa el scaler guardado)

7. **API predice score** (usa el modelo entrenado)

8. **API ordena técnicos** por score (mayor a menor)

9. **API retorna JSON** con técnicos ordenados

---

## 📡 Cómo Probar en Postman

### **Paso 1: Verificar que la API está corriendo**

**GET** `http://localhost:5005/`

**Headers:**
```
(No se requieren headers especiales)
```

**Respuesta esperada:**
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

---

### **Paso 2: Verificar salud del servicio**

**GET** `http://localhost:5005/health`

**Respuesta esperada:**
```json
{
  "status": "ok",
  "modelo_cargado": true,
  "scaler_cargado": true,
  "modelo_disponible": true
}
```

**⚠️ Si `modelo_disponible` es `false`:**
- Ejecuta `python train_model.py` primero

---

### **Paso 3: Obtener Recomendaciones (PRINCIPAL)**

**POST** `http://localhost:5005/recomendar`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "id_solicitud": 1
}
```

**Ejemplo con diferentes IDs:**
```json
{
  "id_solicitud": 123
}
```

```json
{
  "id_solicitud": 5
}
```

**Respuesta exitosa (200 OK):**
```json
{
  "id_solicitud": 1,
  "tecnicos_recomendados": [
    {
      "id_tecnico": 15,
      "distancia_km": 2.5,
      "rating_promedio": 4.8,
      "historico_rating": 4.7,
      "cantidad_calificaciones": 25,
      "precio_promedio": 45000.0,
      "ofertas_totales": 30,
      "servicios_realizados": 50,
      "disponibilidad": 1,
      "score": 0.9234
    },
    {
      "id_tecnico": 8,
      "distancia_km": 5.2,
      "rating_promedio": 4.6,
      "historico_rating": 4.5,
      "cantidad_calificaciones": 20,
      "precio_promedio": 48000.0,
      "ofertas_totales": 25,
      "servicios_realizados": 45,
      "disponibilidad": 1,
      "score": 0.8567
    },
    {
      "id_tecnico": 22,
      "distancia_km": 8.1,
      "rating_promedio": 4.4,
      "historico_rating": 4.3,
      "cantidad_calificaciones": 15,
      "precio_promedio": 50000.0,
      "ofertas_totales": 20,
      "servicios_realizados": 35,
      "disponibilidad": 1,
      "score": 0.7892
    }
  ],
  "total": 3
}
```

**⚠️ Respuesta si no hay técnicos disponibles (200 OK, lista vacía):**
```json
{
  "id_solicitud": 999,
  "tecnicos_recomendados": [],
  "total": 0
}
```

**❌ Errores posibles:**

**400 Bad Request - Falta id_solicitud:**
```json
{
  "error": "id_solicitud requerido"
}
```

**400 Bad Request - JSON vacío:**
```json
{
  "error": "No se recibieron datos"
}
```

**503 Service Unavailable - Modelo no cargado:**
```json
{
  "error": "Modelo no disponible. Ejecuta train_model.py primero",
  "message": "El modelo de machine learning no está cargado. Por favor, entrena el modelo primero."
}
```

**500 Internal Server Error - Error en BD o procesamiento:**
```json
{
  "error": "Error al cargar modelo: modelo_recomendacion.pkl no encontrado. Ejecuta train_model.py primero."
}
```

---

## 📊 Interpretación de Resultados

### **¿Qué significa el score?**

El **score** es un número que indica qué tan bueno es un técnico para esa solicitud específica.

- **Score más alto** = Mejor recomendación
- **Score más bajo** = Recomendación menos ideal

**Ejemplo:**
- Técnico A: `score: 0.9234` → **Mejor opción** ⭐
- Técnico B: `score: 0.8567` → Buena opción
- Técnico C: `score: 0.7892` → Opción aceptable

### **¿Por qué este técnico tiene mejor score?**

El modelo aprende patrones complejos. Por ejemplo:

**Técnico con score alto (0.92):**
- ✅ Cercano (2.5 km)
- ✅ Alta calificación (4.8)
- ✅ Muchas calificaciones (25)
- ✅ Precio razonable (45,000)
- ✅ Mucha experiencia (50 servicios)

**Técnico con score bajo (0.78):**
- ⚠️ Más lejano (8.1 km)
- ⚠️ Calificación un poco menor (4.4)
- ⚠️ Menos calificaciones (15)
- ⚠️ Precio más alto (50,000)

---

## 🔍 Ejemplo Práctico Completo

### **Escenario: Cliente necesita un técnico para reparar su refrigerador**

1. **Cliente crea solicitud en el sistema:**
   - `id_solicitud = 1`
   - Ubicación: lat=4.6097, lon=-74.0817 (Bogotá)
   - Categoría: Electrodomésticos

2. **Sistema busca técnicos disponibles:**
   - Técnico A: Ubicado a 2.5 km, rating 4.8, precio 45,000
   - Técnico B: Ubicado a 5.2 km, rating 4.6, precio 48,000
   - Técnico C: Ubicado a 8.1 km, rating 4.4, precio 50,000

3. **Sistema calcula features:**
   ```
   Técnico A:
   - distancia_km: 2.5
   - rating_promedio: 4.8
   - historico_rating: 4.7
   - cantidad_calificaciones: 25
   - precio_promedio: 45000
   - ofertas_totales: 30
   - servicios_realizados: 50
   - disponibilidad: 1
   ```

4. **Sistema normaliza y predice:**
   - Modelo ML analiza todas las features
   - Predice score: 0.9234 para Técnico A

5. **Sistema ordena y retorna:**
   - Técnico A (score: 0.92) → Primera opción
   - Técnico B (score: 0.86) → Segunda opción
   - Técnico C (score: 0.79) → Tercera opción

6. **Cliente recibe recomendaciones ordenadas** y puede elegir

---

## 🎓 Conceptos Clave

### **1. Learning to Rank**
- El modelo no predice un valor, predice un **orden**
- Aprende a decir: "Este técnico es mejor que este otro para esta solicitud"

### **2. Features Engineering**
- Convertimos datos crudos (lat, lon, calificaciones) en features útiles (distancia, rating promedio)
- Esto ayuda al modelo a entender mejor los patrones

### **3. Normalización (Scaler)**
- Las features tienen diferentes escalas (distancia en km, precio en pesos, rating 0-5)
- El scaler las normaliza para que el modelo pueda compararlas mejor

### **4. Score de Ranking**
- No es una probabilidad (0-1)
- Es un valor relativo: "Mayor = Mejor"
- El modelo aprende a asignar scores altos a técnicos que fueron seleccionados históricamente

---

## 🚀 Checklist para Probar

- [ ] PostgreSQL corriendo
- [ ] Archivo `.env` configurado
- [ ] Ejecutado `python build_dataset.py` (genera dataset)
- [ ] Ejecutado `python train_model.py` (entrena modelo)
- [ ] Ejecutado `python app.py` (inicia API)
- [ ] Probado `GET /health` (verifica modelo cargado)
- [ ] Probado `POST /recomendar` con `id_solicitud` válido

---

## 💡 Tips

1. **El score es relativo**: No compares scores de diferentes solicitudes
2. **Más features = Mejor modelo**: Si tienes más datos históricos, el modelo será más preciso
3. **Actualiza el modelo**: Si agregas muchos datos nuevos, re-entrena el modelo
4. **Verifica disponibilidad**: El sistema solo recomienda técnicos disponibles
5. **Distancia importa**: Técnicos cercanos suelen tener mejor score

---

¿Tienes dudas? ¡Pregunta! 🚀

