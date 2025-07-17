# Sistema de Monitoreo de Temperatura en Tiempo Real para Transporte de Alimentos

## Descripción

Este proyecto implementa una **plataforma web** para monitorear la **temperatura** en tiempo real en camiones de transporte de alimentos perecibles. El sistema asegura que la cadena de frío sea respetada durante el transporte de productos como carnes, frutas y vegetales, enviando alertas automáticas cuando la temperatura excede los rangos configurados. Además, genera **reportes automáticos** al finalizar cada viaje.

La solución está construida sobre un backend en **FastAPI** y un frontend accesible mediante un navegador web. La información se transmite desde un sensor de temperatura conectado a un **Arduino** hacia un servidor en **AWS EC2**.

## Tecnologías Utilizadas

- **Backend**: FastAPI (Python)
- **Frontend**: HTML, Jinja2 (usado por FastAPI para generar plantillas web)
- **Base de datos**: Archivos JSON (para almacenar información de usuarios y registros históricos)
- **Contenerización**: Docker
- **Infraestructura en la nube**: AWS EC2
- **Comunicaciones**: Protocolo HTTP (API REST)
- **Lenguaje de programación**: Python
- **Sensor**: Arduino (DHT22 o similar) para la lectura de temperatura

## Funcionalidades

- **Monitoreo en tiempo real** de la temperatura en el interior de los camiones.
- **Alertas automáticas** cuando la temperatura supera los rangos configurados.
- **Generación de reportes** al finalizar cada viaje, incluyendo gráficos de temperatura y registros de alertas.
- **Gestión de usuarios**: Administradores pueden crear usuarios y ver reportes históricos.
- **Despliegue remoto**: Sistema desplegado en la nube usando AWS EC2, accesible desde cualquier lugar.

## Requisitos

- **Python 3.8+**
- **FastAPI**: Framework web para construir la API REST.
- **Uvicorn**: Servidor ASGI para ejecutar FastAPI.
- **Docker**: Para la contenerización del sistema.
- **AWS EC2**: Para desplegar el sistema en la nube.
- **Arduino**: Para obtener los datos de temperatura.

## Instalación

1. **Clona este repositorio**:

   ```bash
   git clone https://github.com/jeysanty/sistema_monitoreo_temp.git
