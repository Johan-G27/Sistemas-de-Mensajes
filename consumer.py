import pika
import psycopg2
import json
import time
from datetime import datetime
from datetime import timezone
from prometheus_client import start_http_server, Counter

# Conectar a RabbitMQ
def connect_to_rabbitmq():
    while True:
        try:
            # Intentar la conexión
            credentials = pika.PlainCredentials('admin', 'admin')  # Cambia 'admin' y 'admin' si es necesario
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672, '/', credentials=credentials))  # Cambiado localhost por rabbitmq
            channel = connection.channel()

            # Declarar un exchange durable
            channel.exchange_declare(exchange='weather_exchange', exchange_type='direct', durable=True)

            # Declarar la cola durable
            channel.queue_declare(queue='weather_data_queue', durable=True)

            # Bindear la cola al exchange con el routing_key sin el prefijo 'station.'
            
            channel.queue_bind(exchange='weather_exchange', queue='weather_data_queue', routing_key='Barranquilla')
            channel.queue_bind(exchange='weather_exchange', queue='weather_data_queue', routing_key='Bogotá')
            channel.queue_bind(exchange='weather_exchange', queue='weather_data_queue', routing_key='Medellín')
            channel.queue_bind(exchange='weather_exchange', queue='weather_data_queue', routing_key='Cartagena')
            channel.queue_bind(exchange='weather_exchange', queue='weather_data_queue', routing_key='Cali')

            print("Conexión a RabbitMQ exitosa y cola declarada.")
            return channel

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error de conexión a RabbitMQ: {e}. Intentando nuevamente en 5 segundos...")
            time.sleep(5)  # Esperar 5 segundos antes de intentar de nuevo


# Conectar a PostgreSQL
def connect_to_postgres():
    conn = psycopg2.connect(
        host="postgres",  # 'postgres' es el nombre del contenedor de PostgreSQL en Docker
        database="weather_db",
        user="postgres",
        password="password"
    )
    return conn

# Crear la tabla si no existe
def create_table_if_not_exists():
    conn = connect_to_postgres()
    cursor = conn.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS weather_logs (
        id SERIAL PRIMARY KEY,
        station_id VARCHAR(255) NOT NULL,
        temperature FLOAT NOT NULL,
        humidity FLOAT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL
    );
    """
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()

# Procesar los mensajes
def process_message(ch, method, _, body):
    try:
        data = json.loads(body)
        print(f"Recibido mensaje de la estación {data['station_id']}")

        # Validar los datos (por ejemplo, temperatura entre -10 y 50 grados)
        if not (-10 <= data['temperature'] <= 50):
            print("Error: Temperatura fuera de rango")
            ch.basic_nack(delivery_tag=method.delivery_tag)  # No confirmar el mensaje
            return

        # Crear la tabla si no existe
        create_table_if_not_exists()

        # Persistir en PostgreSQL
        conn = connect_to_postgres()
        cursor = conn.cursor()
        insert_query = """INSERT INTO weather_logs (station_id, temperature, humidity, timestamp)
                          VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_query, (data['station_id'], data['temperature'], data['humidity'], datetime.now(timezone.utc).isoformat()))
        conn.commit()
        cursor.close()
        conn.close()

        # Confirmar el mensaje
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Confirmar que el mensaje fue procesado
        print(f"Datos de la estación {data['station_id']} guardados exitosamente")

    except json.JSONDecodeError as e:
        print(f"Error al procesar el mensaje, JSON no válido: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

# Métricas de ejemplo
messages_sent = Counter('producer_messages_sent_total', 'Total de mensajes enviados')
errors = Counter('producer_errors_total', 'Errores en el producer')

# Inicia el servidor de métricas
start_http_server(8000)

# Conectar a RabbitMQ y comenzar a consumir
channel = connect_to_rabbitmq()
channel.basic_consume(queue='weather_data_queue', on_message_callback=process_message)
channel.start_consuming()