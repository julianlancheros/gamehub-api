from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN DE MONGODB
# ============================================

# Leer la URL desde variable de entorno o usar la directa
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://gamehub_user:GameHub2026!@gamehub-cluster.pwnljj1.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true')

try:
    # Conectar a MongoDB con opciones SSL
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    # Probar conexión
    client.admin.command('ping')
    db = client['gamehub_stats']
    coleccion = db['estadisticas']
    print("✅ Conectado a MongoDB Atlas")
except Exception as e:
    print(f"❌ Error de conexión a MongoDB: {e}")
    coleccion = None

# ============================================
# ENDPOINT 1: Registrar información analítica
# ============================================
@app.route('/api/videojuegos', methods=['POST'])
def registrar_estadisticas():
    """
    Recibe datos de una reseña desde PHP y actualiza las estadísticas en MongoDB
    """
    print("📥 Recibida petición POST")
    try:
        # Recibir datos del cuerpo de la solicitud (JSON)
        datos = request.json
        print(f"📦 Datos recibidos: {datos}")
        
        # Validar que llegaron todos los datos necesarios
        if not datos:
            print("❌ No se recibieron datos")
            return jsonify({"error": "No se recibieron datos"}), 400
        
        # OBTENER Y CONVERTIR VIDEOJUEGO_ID A NÚMERO
        try:
            videojuego_id = int(datos.get('videojuego_id'))
        except (TypeError, ValueError):
            print("❌ videojuego_id no es un número válido")
            return jsonify({"error": "videojuego_id debe ser un número"}), 400
        
        titulo = datos.get('titulo', 'Sin título')
        
        # OBTENER Y CONVERTIR CALIFICACION A NÚMERO
        try:
            calificacion = int(datos.get('calificacion', 0))
        except (TypeError, ValueError):
            print("❌ calificacion no es un número válido")
            return jsonify({"error": "calificacion debe ser un número"}), 400
        
        print(f"🔍 Buscando juego ID: {videojuego_id}")
        
        # Verificar conexión a MongoDB
        if coleccion is None:
            print("❌ No hay conexión a MongoDB")
            return jsonify({"error": "Error de conexión a MongoDB"}), 500
        
        # Buscar el juego en MongoDB
        juego = coleccion.find_one({"videojuego_id": videojuego_id})
        print(f"📊 Juego encontrado: {juego}")
        
        if juego:
            # Si el juego ya existe, actualizar estadísticas
            nuevas_resenas = juego.get('total_reseñas', 0) + 1
            promedio_anterior = juego.get('promedio_calificacion', 0)
            total_anterior = juego.get('total_reseñas', 0)
            nuevo_promedio = ((promedio_anterior * total_anterior) + calificacion) / nuevas_resenas
            
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
            print("✅ Estadísticas actualizadas")
            return jsonify({"mensaje": "Estadísticas actualizadas", "videojuego_id": videojuego_id}), 201
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
            print("✅ Nuevo juego registrado")
            return jsonify({"mensaje": "Juego registrado en estadísticas", "videojuego_id": videojuego_id}), 201
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
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
        if coleccion is None:
            return jsonify({"error": "Error de conexión a MongoDB"}), 500
        
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
        if coleccion is None:
            return jsonify({"error": "Error de conexión a MongoDB"}), 500
        
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
