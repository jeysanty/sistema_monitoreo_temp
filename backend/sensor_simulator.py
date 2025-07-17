import requests
import time
import serial
from datetime import datetime

# URL del backend FastAPI (ajusta si usas localhost o IP pública diferente)
API_URL = "http://3.19.143.4:8000/temperature"

# Configurar el puerto serial para leer los datos de Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600)  # Cambia el puerto a tu configuración
time.sleep(2)  # Espera para establecer la conexión serial

def enviar_temperatura():
    while True:
        if ser.in_waiting > 0:  # Verifica si hay datos disponibles
            # Leer los datos enviados por Arduino (temperatura, humedad)
            datos = ser.readline().decode('utf-8').strip()
            # Suponiendo que Arduino envía: "23.5,60"
            temperatura, humedad = datos.split(',')
            timestamp = datetime.utcnow().isoformat()  # UTC para evitar errores de zona horaria
            data = {
                "valor": round(float(temperatura), 2),
                "timestamp": timestamp
            }

            try:
                # Enviar los datos al API
                response = requests.post(API_URL, json=data, headers={"Content-Type": "application/json"})
                print(f"[{timestamp}] Enviado: {temperatura} °C -> {response.status_code} {response.text}")
            except Exception as e:
                print(f"❌ Error al enviar: {e}")

        time.sleep(5)  # espera 5 segundos entre envíos

if __name__ == "__main__":
    enviar_temperatura()
