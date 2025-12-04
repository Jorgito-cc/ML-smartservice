from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
from recommender import recomendar_tecnicos

app = Flask(__name__)
CORS(app)

# Variables globales para modelo y scaler (carga lazy)
modelo = None
scaler = None

def cargar_modelo():
    """Carga el modelo y scaler si existen"""
    global modelo, scaler
    try:
        if os.path.exists("modelo_recomendacion.pkl") and os.path.exists("scaler.pkl"):
            modelo = joblib.load("modelo_recomendacion.pkl")
            scaler = joblib.load("scaler.pkl")
            print("✅ Modelo y scaler cargados correctamente")
        else:
            print("⚠ Modelo o scaler no encontrados. Ejecuta train_model.py primero")
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")

# Cargar modelo al iniciar la aplicación
cargar_modelo()

@app.route("/", methods=["GET"])
def home():
    """Endpoint raíz - información del servicio"""
    return jsonify({
        "message": "💡 API ML funcionando.",
        "modelo_cargado": modelo is not None,
        "scaler_cargado": scaler is not None,
        "endpoints": {
            "/": "Información del servicio",
            "/recomendar": "POST - Recomendar técnicos para una solicitud",
            "/health": "GET - Estado de salud del servicio"
        }
    })

@app.route("/recomendar", methods=["POST"])
def recomendar():
    """
    Endpoint para recomendar técnicos para una solicitud.
    
    Request Body:
        {
            "id_solicitud": int
        }
    
    Response:
        {
            "id_solicitud": int,
            "tecnicos_recomendados": [...],
            "total": int
        }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        id_solicitud = data.get("id_solicitud")
        
        if not id_solicitud:
            return jsonify({"error": "id_solicitud requerido"}), 400
        
        if modelo is None or scaler is None:
            return jsonify({
                "error": "Modelo no disponible. Ejecuta train_model.py primero",
                "message": "El modelo de machine learning no está cargado. Por favor, entrena el modelo primero."
            }), 503
        
        resultados = recomendar_tecnicos(id_solicitud)
        
        return jsonify({
            "id_solicitud": id_solicitud,
            "tecnicos_recomendados": resultados,
            "total": len(resultados)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    """Endpoint de salud del servicio"""
    return jsonify({
        "status": "ok",
        "modelo_cargado": modelo is not None,
        "scaler_cargado": scaler is not None,
        "modelo_disponible": modelo is not None and scaler is not None
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
