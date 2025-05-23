import requests
import json
import time
import pika
from datetime import datetime
from datetime import timezone
import urllib.parse  
from prometheus_client import start_http_server, Counter

# Reemplaza 'tu_clave_de_api' con tu clave real de API obtenida de OpenWeatherMap
API_KEY = '6d4197a3f96316ac680feb27fe512c44'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

# Conexión a RabbitMQ
def connect_to_rabbitmq():
    while True:
        try:
            # Intentar la conexión
            credentials = pika.PlainCredentials('admin', 'admin') 
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672, '/', credentials=credentials)) 
            channel = connection.channel()

            # Declarar un exchange durable
            channel.exchange_declare(exchange='weather_exchange', exchange_type='direct', durable=True)

            # Declarar la cola durable
            channel.queue_declare(queue='weather_data_queue', durable=True)  # Declarar la cola aquí

            print("Conexión a RabbitMQ exitosa.")
            return channel

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error de conexión a RabbitMQ: {e}. Intentando nuevamente en 5 segundos...")
            time.sleep(5)  # Esperar 5 segundos antes de intentar de nuevo

# Función para obtener los datos meteorológicos usando la API de OpenWeatherMap
def get_weather_data(station_id):
    # Codificar el nombre de la ciudad correctamente para manejar caracteres especiales
    city_name = urllib.parse.quote(station_id)
    
    # URL para la solicitud a OpenWeatherMap
    url = f'{BASE_URL}?q={city_name}&appid={API_KEY}&units=metric'
    
    try:
        # Hacer la solicitud HTTP a la API de OpenWeatherMap
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si la respuesta fue 4xx o 5xx
        weather_data = response.json()

        # Extraer datos relevantes si la respuesta es exitosa
        data = {
            "station_id": station_id,
            "temperature": weather_data['main']['temp'],  # Temperatura actual
            "humidity": weather_data['main']['humidity'],        # Humedad actual
            "timestamp": datetime.now(timezone.utc).isoformat()               # Timestamp actual
        }
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos para {station_id}: {e}")
        return None

# Función para enviar los datos a RabbitMQ
def send_data_to_rabbitmq(channel, data):
    try:
        channel.basic_publish(
            exchange='weather_exchange',
            routing_key=data['station_id'],
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2  # Hacer el mensaje durable
            )
        )
        print(f"Datos enviados para la estación {data['station_id']}")
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error al enviar datos a RabbitMQ: {e}")

# Conectar a RabbitMQ
channel = connect_to_rabbitmq()

# Ciudades de Colombia
stations = ["Bogotá", "Medellín", "Cartagena", "Cali", "Barranquilla"]

# Métricas de ejemplo
messages_sent = Counter('producer_messages_sent_total', 'Total de mensajes enviados')
errors = Counter('producer_errors_total', 'Errores en el producer')

# Inicia el servidor de métricas
start_http_server(8000)  # o 8001 para consumer

# Ciclo para enviar datos cada 1 segundo
while True:
    for station in stations:
        weather_data = get_weather_data(station)
        if weather_data:
            send_data_to_rabbitmq(channel, weather_data)
        time.sleep(1)  # Pausar 1 segundo antes de obtener los datos para la siguiente ciudad
