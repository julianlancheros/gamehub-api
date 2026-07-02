from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# Configurar la conexión a MongoDB
# ⚠️ IMPORTANTE: Reemplaza con tu URL de MongoDB
MONGO_URI = "mongodb+srv://gamehub_user:GameHub2026!@gamehub-cluster.pwnljj1.mongodb.net/"

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client['gamehub_stats']  # Base de datos
coleccion = db['estadisticas']  # Colección

print("✅ Conectado a MongoDB Atlas")

# ============================================
# ENDPOINT 1: Registrar información analítica
# ============================================
@app.route('/api/videojuegos', methods=['POST'])
def registrar_estadisticas():
    """
    Recibe datos de una reseña desde PHP y actualiza las estadísticas en MongoDB
    """
    try:
        # Recibir datos del cuerpo de la solicitud (JSON)
        datos = request.json
        
        # Validar que llegaron todos los datos necesarios
        if not datos or 'videojuego_id' not in datos:
            return jsonify({"error": "Faltan datos obligatorios"}), 400
        
        videojuego_id = datos['videojuego_id']
        titulo = datos.get('titulo', 'Sin título')
        calificacion = datos.get('calificacion', 0)
        
        # Buscar el juego en MongoDB
        juego = coleccion.find_one({"videojuego_id": videojuego_id})
        
        if juego:
            # Si el juego ya existe, actualizar estadísticas
            nuevas_resenas = juego.get('total_reseñas', 0) + 1
            nuevo_promedio = ((juego.get('promedio_calificacion', 0) * juego.get('total_reseñas', 0)) + calificacion) / nuevas_resenas
            
            # Actualizar en MongoDB
            coleccion.update_one(
                {"videojuego_id": videojuego_id},
                {"$set": {
                    "titulo": titulo,
                    "total_reseñas": nuevas_resenas,
                    "promedio_calificacion": round(nuevo_promedio, 2),
                    "ultima_actualizacion": datetime.now().isoformat()
                }}
            )
            mensaje = "Estadísticas actualizadas"
        else:
            # Si el juego no existe, crearlo
            nuevo_juego = {
                "videojuego_id": videojuego_id,
                "titulo": titulo,
                "total_reseñas": 1,
                "promedio_calificacion": calificacion,
                "ultima_actualizacion": datetime.now().isoformat()
            }
            coleccion.insert_one(nuevo_juego)
            mensaje = "Juego registrado en estadísticas"
        
        return jsonify({"mensaje": mensaje, "videojuego_id": videojuego_id}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ENDPOINT 2: Consultar estadísticas
# ============================================
@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """
    Devuelve todas las estadísticas de todos los juegos
    """
    try:
        # Obtener todos los juegos de MongoDB
        juegos = list(coleccion.find({}, {"_id": 0}))  # Excluir el campo _id
        
        if not juegos:
            return jsonify({"mensaje": "No hay estadísticas disponibles"}), 200
        
        return jsonify({"estadisticas": juegos}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# ENDPOINT 3: Videojuegos mejor calificados
# ============================================
@app.route('/api/mejores-videojuegos', methods=['GET'])
def mejores_videojuegos():
    """
    Devuelve los 5 juegos mejor calificados
    """
    try:
        # Obtener juegos ordenados por promedio (de mayor a menor)
        juegos = list(coleccion.find({}, {"_id": 0})
                     .sort("promedio_calificacion", -1)
                     .limit(5))
        
        if not juegos:
            return jsonify({"mensaje": "No hay juegos registrados"}), 200
        
        return jsonify({"mejores": juegos}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# Endpoint de prueba
# ============================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "mensaje": "API de GameHub funcionando 🎮",
        "endpoints": {
            "POST /api/videojuegos": "Registrar estadísticas de un juego",
            "GET /api/estadisticas": "Ver todas las estadísticas",
            "GET /api/mejores-videojuegos": "Ver los 5 mejores juegos"
        }
    })

# ============================================
# Iniciar el servidor
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)