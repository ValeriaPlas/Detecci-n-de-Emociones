"""
OBJETIVO DEL CÓDIGO
------------------
Este programa implementa una API REST utilizando FastAPI que recibe una imagen
enviada desde un dispositivo externo (por ejemplo, una ESP32-CAM), la procesa
utilizando OpenCV y analiza las emociones faciales presentes en la imagen
mediante la librería DeepFace.

El sistema decodifica la imagen recibida, la muestra en tiempo real en una
ventana local y posteriormente extrae las emociones detectadas, devolviendo
como respuesta la emoción dominante y el porcentaje de cada emoción identificada.
"""

from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
from deepface import DeepFace
import tempfile

# Comando para ejecutar el servidor:
# uvicorn main:app --host 0.0.0.0 --port 8000

# Crear la aplicación FastAPI
app = FastAPI()


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Endpoint que recibe una imagen mediante una solicitud POST,
    analiza las emociones faciales presentes y devuelve los resultados
    en formato JSON.
    
    Parámetros:
    - file: imagen enviada como archivo (UploadFile)
    
    Retorna:
    - Emoción dominante detectada
    - Diccionario con todas las emociones y sus probabilidades
    """
    try:
        # Leer el contenido del archivo recibido (bytes)
        contents = await file.read()

        # Convertir los bytes a un arreglo de numpy
        np_arr = np.frombuffer(contents, np.uint8)

        # Decodificar la imagen a formato OpenCV (BGR)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Mostrar la imagen recibida en una ventana local
        cv2.imshow("Imagen ESP32-CAM", img)
        cv2.waitKey(1)  # Permite refrescar la ventana sin bloquear el programa

        # Crear un archivo temporal para que DeepFace pueda analizar la imagen
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(contents)
            path = tmp.name

        # Analizar emociones utilizando DeepFace
        result = DeepFace.analyze(
            img_path=path,
            actions=["emotion"],      # Solo se analizan emociones
            enforce_detection=False   # Evita errores si no se detecta un rostro
        )

        # DeepFace puede devolver una lista, se extrae el primer resultado
        if isinstance(result, list):
            result = result[0]

        # Convertir las emociones a tipo float para evitar errores de serialización
        emotions = {
            k: float(v) for k, v in result["emotion"].items()
        }

        # Respuesta en formato JSON
        return {
            "dominant_emotion": result["dominant_emotion"],
            "emotions": emotions
        }

    except Exception as e:
        # Mostrar error en consola y devolver mensaje al cliente
        print("ERROR:", e)
        return {"error": str(e)}
