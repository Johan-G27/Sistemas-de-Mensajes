# Usar una imagen base de Python
FROM python:3.13

RUN apt-get update && \
    apt-get install -y libpq-dev build-essential

# Crear un directorio para el proyecto dentro del contenedor
WORKDIR /app

# Copiar el contenido del proyecto al contenedor
COPY . /app

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt





