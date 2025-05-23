# Proyecto Meteorología - Sistema de Microservicios con Monitoreo

Por: Johan Grimaldos; Miguel Baranoa; Jorge Mercado

Este proyecto implementa un sistema basado en microservicios para la adquisición, procesamiento y almacenamiento de datos meteorológicos en tiempo real. Utiliza tecnologías como RabbitMQ para la mensajería, PostgreSQL para la base de datos, Prometheus y Grafana para monitoreo, y Ofelia para la orquestación de tareas.

---

## Arquitectura del Sistema

El sistema está compuesto por los siguientes componentes principales:

- **Productor (Producer):** Obtiene datos meteorológicos desde la API de OpenWeatherMap y los publica en RabbitMQ.
- **Cola de Mensajes (RabbitMQ):** Middleware que permite la comunicación asíncrona entre productor y consumidor.
- **Consumidor (Consumer):** Lee mensajes de RabbitMQ y los persiste en la base de datos PostgreSQL.
- **Base de Datos (PostgreSQL):** Almacena los datos meteorológicos recibidos.
- **Monitoreo (Prometheus y Grafana):** Recolecta métricas de los servicios y las presenta en dashboards gráficos.
- **Orquestador de Tareas (Ofelia):** Programa y ejecuta las tareas periódicas de productor y consumidor.
