# Monitor USD/DOP

Demo de Python y Streamlit: consulta una tasa de referencia USD/DOP, convierte importes y permite exportar hasta 50 lecturas de la sesión. No necesita MySQL. La interfaz se adapta mediante componentes nativos de Streamlit.

## Fuente y límites

[ExchangeRate-API Open Access](https://www.exchangerate-api.com/docs/free) actualiza diariamente. Se muestra la fecha del proveedor, la atribución requerida y una advertencia de que no es una tasa bancaria de compra/venta. La caché compartida consulta como máximo una vez por hora por proceso cuando funciona; ante errores espera un minuto y conserva la última lectura en memoria. El refresco opcional de pantalla ocurre cada minuto mientras la sesión está activa. El gráfico muestra observaciones locales, no datos históricos del mercado.

## Ejecución local

Python 3.11 o superior:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
.venv/bin/python server.py
```

En Windows: `.venv\Scripts\python` en lugar de `.venv/bin/python`. Abrir http://127.0.0.1:8501/. `.env` es opcional; partir de `.env.example` si se usa una subruta. El servidor respeta las variables del proveedor.

## alwaysdata: activar después de la Tabla periódica

```sh
cd ~/apps
git clone https://github.com/Jeison-Rosario/app-dolar.git
cd app-dolar
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
```

Crear un sitio de tipo **programa definido por el usuario / comando personalizado** que ejecute el servidor HTTP de Streamlit (no WSGI). Dirección `bookapp.alwaysdata.net/app-dolar`, directorio de trabajo relativo **`apps/app-dolar`**, comando **`/home/bookapp/apps/app-dolar/.venv/bin/python /home/bookapp/apps/app-dolar/server.py`**, variable **`BASE_PATH=/app-dolar`**. **Desactivar Trim path/recortar ruta**, pues Streamlit gestiona el prefijo de forma nativa. No sobrescribir IP, HOST ni PORT. Mantener las protecciones CORS y XSRF predeterminadas. El proxy debe admitir WebSockets.

Comprobar `/app-dolar/` y `/app-dolar/_stcore/health`, conversión, CSV y funcionamiento con dos sesiones. El despliegue real y la revisión visual quedan pendientes. Vigilar RAM: Streamlit y pandas pueden consumir más memoria que los proyectos Node. Que el panel permita otro sitio no garantiza capacidad para cuatro aplicaciones. Si aparecen fallos, detener solo el nuevo sitio y revisar el consumo. No se ha contratado ningún plan adicional.

## Telegram

Esta versión pública **no envía mensajes** y elimina el token y los destinatarios del código. La integración anterior debe considerarse desactivada. El propietario debe revocar el token antiguo con BotFather: quitarlo del archivo actual no lo elimina del historial de Git. No publicar un nuevo token ni pegarlo en conversaciones. Para recuperar avisos en el futuro, crear un proceso privado programado, con credenciales de entorno y deduplicación persistente; nunca enviar desde las sesiones públicas.

## Estructura

`app.py`: interfaz; `rates.py`: validación, caché y recuperación; `server.py`: arranque; `test_rates.py`: pruebas sin consultas externas ni mensajes; `.env.example`: configuración no sensible.

Versiones comprobadas en Python 3.12: `requirements.lock.txt`. Para reproducirlas usar `pip install -r requirements.lock.txt`; `requirements.txt` mantiene los rangos compatibles para otras versiones de Python.
