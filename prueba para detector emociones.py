"""
OBJETIVO DEL CÓDIGO
------------------
Este programa permite a un dispositivo ESP32-CAM conectarse a una red Wi-Fi,
inicializar su cámara integrada, capturar imágenes de manera periódica y
enviarlas a un servidor web mediante una petición HTTP POST.

Las imágenes capturadas se envían en formato multipart/form-data a un endpoint
específico (/analyze), donde serán procesadas para su análisis (por ejemplo,
detección de emociones faciales mediante inteligencia artificial).
"""

import camera     # Para controlar la cámara del ESP32-CAM
import network    # Para conectarse a redes Wi-Fi
import time       # Para manejar retardos y pausas
import socket     # Para establecer conexión con el servidor web


def conectar_wifi(ssid, password):
    """
    Función para conectar el ESP32-CAM a una red Wi-Fi.

    Parámetros:
    - ssid: Nombre de la red Wi-Fi
    - password: Contraseña de la red Wi-Fi

    Retorna:
    - Dirección IP asignada al dispositivo
    """
    wlan = network.WLAN(network.STA_IF)   # Crear interfaz Wi-Fi en modo estación
    wlan.active(True)                     # Activar la interfaz
    wlan.connect(ssid, password)          # Conectarse a la red

    print('Conectando a la red Wi-Fi...', ssid, password)

    # Esperar hasta que la conexión sea exitosa
    while not wlan.isconnected():
        time.sleep(1)
        print('.', end='')

    print('\n¡Conexión exitosa!')
    print('Dirección IP asignada:', wlan.ifconfig()[0])
    return wlan.ifconfig()[0]


def send_image(img_bytes):
    """
    Envía una imagen al servidor mediante una petición HTTP POST
    usando el formato multipart/form-data.

    Parámetros:
    - img_bytes: Imagen capturada en formato bytes

    Retorna:
    - Respuesta del servidor
    """
    boundary = "ESP32BOUNDARY"
    host = "10.18.206.186"   # IP del servidor FastAPI
    port = 8000
    path = "/analyze"

    # Inicio del cuerpo del mensaje HTTP
    body_start = (
        "--" + boundary + "\r\n"
        "Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n"
        "Content-Type: image/jpeg\r\n\r\n"
    )

    # Fin del cuerpo del mensaje HTTP
    body_end = "\r\n--" + boundary + "--\r\n"

    # Calcular tamaño total del contenido
    content_length = len(body_start) + len(img_bytes) + len(body_end)

    # Crear socket y conectar al servidor
    s = socket.socket()
    s.connect((host, port))

    # Enviar encabezados HTTP
    s.send(
        "POST {} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "Content-Type: multipart/form-data; boundary={}\r\n"
        "Content-Length: {}\r\n"
        "Connection: close\r\n\r\n"
        .format(path, host, boundary, content_length)
    )

    # Enviar el cuerpo de la petición
    s.send(body_start)
    s.send(img_bytes)
    s.send(body_end)

    # Leer la respuesta del servidor
    response = b""
    while True:
        data = s.recv(512)
        if not data:
            break
        response += data

    s.close()
    print(response.decode())
    return response


def inicializar_camara():
    """
    Inicializa la cámara del ESP32-CAM y configura
    el tamaño de la imagen.
    """
    try:
        camera.init()        # Inicializar cámara
        camera.framesize(4) # Resolución aproximada 240x240
        print('Cámara inicializada correctamente.')
    except Exception as e:
        print('Error al inicializar la cámara:', e)


def tomar_foto():
    """
    Captura una imagen utilizando la cámara del ESP32-CAM.

    Retorna:
    - Imagen en formato bytes si la captura fue exitosa
    - None si ocurrió un error
    """
    print('Tomando una foto...')
    try:
        foto = camera.capture()

        if foto is False or foto is None:
            print("Falló la captura")
            return None

        if not isinstance(foto, (bytes, bytearray)):
            print("Tipo inesperado:", type(foto))
            return None

        print('Foto tomada exitosamente.')
        return foto

    except Exception as e:
        print('Error al tomar la foto:', e)
        return None


# ==============================
# CONFIGURACIÓN PRINCIPAL
# ==============================

# Datos de la red Wi-Fi
ssid = 'SM-G960UA47'
password = 'SailorMoon'

# Paso 1: Conectarse a la red Wi-Fi
ip = conectar_wifi(ssid, password)

# Paso 2: Inicializar la cámara
inicializar_camara()

# Paso 3: Tomar y enviar fotos periódicamente
while True:
    time.sleep(5)            # Esperar 5 segundos entre capturas
    foto = tomar_foto()
    if foto is not None:
        resp = send_image(foto)
        print(resp.decode())
