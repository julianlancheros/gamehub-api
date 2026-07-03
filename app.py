from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import traceback

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN DE MONGODB
# ============================================

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://gamehub_user:GameHub2026!@gamehub-cluster.pwnljj1.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true')

try:
    print("🔄 Conectando a MongoDB...")
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    client.admin.command('ping')
    db = client['gamehub_stats']
    coleccion = db['estadisticas']
    print("✅ Conectado a MongoDB Atlas")
except Exception as e:
    print(f"❌ Error de conexión a MongoDB: {e}")
    coleccion = None

# ============================================
# ENDPOINT 1: Registrar estadísticas
# ============================================
@app.route('/api/videojuegos', methods=['POST'])
def registrar_estadisticas():
    print("📥 Recibida petición POST")
    try:
        # Obtener datos JSON
        datos = request.get_json()
        print(f"📦 Datos recibidos: {datos}")
        
        # Validar que hay datos
        if datos is None:
            print("❌ No se recibió JSON válido")
            return jsonify({"error": "No se recibió JSON válido"}), 400
        
        # Verificar que el campo existe
        if 'videojuego_id' not in datos:
            print("❌ Falta videojuego_id")
            return jsonify({"error": "Falta videojuego_id"}), 400
        
        # ✅ CONVERTIR VIDEOJUEGO_ID A NÚMERO
        try:
            videojuego_id = int(datos['videojuego_id'])
        except (TypeError, ValueError):
            print("❌ videojuego_id no es un número válido")
            return jsonify({"error": "videojuego_id debe ser un número"}), 400
        
        titulo = datos.get('titulo', 'Sin título')
        
        # ✅ CONVERTIR CALIFICACION A NÚMERO (¡SOLUCIÓN DEL ERROR!)
        try:
            calificacion = int(datos.get('calificacion', 0))
        except (TypeError, ValueError):
            print("❌ calificacion no es un número válido")
            return jsonify({"error": "calificacion debe ser un número"}), 400
        
        print(f"🔍 Procesando: ID={videojuego_id}, Título={titulo}, Calificación={calificacion}")
        
        # Verificar conexión a MongoDB
        if coleccion is None:
            print("❌ No hay conexión a MongoDB")
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        
        # Buscar el juego
        juego = coleccion.find_one({"videojuego_id": videojuego_id})
        print(f"📊 Juego encontrado: {juego}")
        
        if juego:
            # Actualizar juego existente
            total_actual = juego.get('total_reseñas', 0)
            promedio_actual = juego.get('promedio_calificacion', 0)
            nuevo_total = total_actual + 1
            # ✅ AHORA calificacion es un número
            nuevo_promedio = ((promedio_actual * total_actual) + calificacion) / nuevo_total
            
            coleccion.update_one(
                {"videojuego_id": videojuego_id},
                {"$set": {
                    "titulo": titulo,
                    "total_reseñas": nuevo_total,
                    "promedio_calificacion": round(nuevo_promedio, 2),
                    "ultima_actualizacion": datetime.now().isoformat()
                }}
            )
            print("✅ Estadísticas actualizadas")
            return jsonify({
                "mensaje": "Estadísticas actualizadas",
                "videojuego_id": videojuego_id,
                "total_reseñas": nuevo_total,
                "promedio": round(nuevo_promedio, 2)
            }), 201
        else:
            # Crear nuevo juego
            nuevo_documento = {
                "videojuego_id": videojuego_id,
                "titulo": titulo,
                "total_reseñas": 1,
                "promedio_calificacion": calificacion,
                "ultima_actualizacion": datetime.now().isoformat()
            }
            coleccion.insert_one(nuevo_documento)
            print("✅ Nuevo juego registrado")
            return jsonify({
                "mensaje": "Juego registrado en estadísticas",
                "videojuego_id": videojuego_id
            }), 201
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ============================================
# ENDPOINT 2: Consultar estadísticas
# ============================================
@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    try:
        if coleccion is None:
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        juegos = list(coleccion.find({}, {"_id": 0}))
        return jsonify({"estadisticas": juegos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ENDPOINT 3: Mejores juegos
# ============================================
@app.route('/api/mejores-videojuegos', methods=['GET'])
def mejores_videojuegos():
    try:
        if coleccion is None:
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        juegos = list(coleccion.find({}, {"_id": 0}).sort("promedio_calificacion", -1).limit(5))
        return jsonify({"mejores": juegos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# Inicio
# ============================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "mensaje": "API de GameHub funcionando 🎮",
        "endpoints": {
            "POST /api/videojuegos": "Registrar estadísticas",
            "GET /api/estadisticas": "Ver estadísticas",
            "GET /api/mejores-videojuegos": "Top 5 juegos"
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)sonify({
        "mensaje": "API de GameHub funcionando 🎮",
        "endpoints": {
            "POST /api/videojuegos": "Registrar estadísticas",
            "GET /api/estadisticas": "Ver estadísticas",
            "GET /api/mejores-videojuegos": "Top 5 juegos"
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
