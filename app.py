from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
import traceback

app = Flask(__name__)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://gamehub_user:GameHub2026!@gamehub-cluster.pwnlj1.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true')

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

@app.route('/api/videojuegos', methods=['POST'])
def registrar_estadisticas():
    print("📥 Recibida petición POST")
    try:
        datos = request.get_json()
        print(f"📦 Datos recibidos: {datos}")
        
        if datos is None:
            return jsonify({"error": "No se recibió JSON válido"}), 400
        
        if 'videojuego_id' not in datos:
            return jsonify({"error": "Falta videojuego_id"}), 400
        
        # ✅ CONVERTIR A NÚMERO
        try:
            videojuego_id = int(datos['videojuego_id'])
        except:
            return jsonify({"error": "videojuego_id debe ser un número"}), 400
        
        titulo = datos.get('titulo', 'Sin título')
        
        # ✅ CONVERTIR CALIFICACION A NÚMERO (¡ESTA ES LA SOLUCIÓN!)
        try:
            calificacion = int(datos.get('calificacion', 0))
        except:
            return jsonify({"error": "calificacion debe ser un número"}), 400
        
        print(f"🔍 ID={videojuego_id}, Calificación={calificacion}")
        
        if coleccion is None:
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        
        juego = coleccion.find_one({"videojuego_id": videojuego_id})
        
        if juego:
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
            return jsonify({"mensaje": "Estadísticas actualizadas"}), 201
        else:
            nuevo_documento = {
                "videojuego_id": videojuego_id,
                "titulo": titulo,
                "total_reseñas": 1,
                "promedio_calificacion": calificacion,
                "ultima_actualizacion": datetime.now().isoformat()
            }
            coleccion.insert_one(nuevo_documento)
            return jsonify({"mensaje": "Juego registrado en estadísticas"}), 201
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    try:
        if coleccion is None:
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        juegos = list(coleccion.find({}, {"_id": 0}))
        return jsonify({"estadisticas": juegos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mejores-videojuegos', methods=['GET'])
def mejores_videojuegos():
    try:
        if coleccion is None:
            return jsonify({"error": "No hay conexión a MongoDB"}), 500
        juegos = list(coleccion.find({}, {"_id": 0}).sort("promedio_calificacion", -1).limit(5))
        return jsonify({"mejores": juegos}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    app.run(debug=True, host='0.0.0.0', port=5000)
