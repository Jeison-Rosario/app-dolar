# Conversor de divisas

Demo de Python y Streamlit: convierte entre las monedas disponibles del proveedor con selectores de origen/destino e intercambio rápido; empieza en USD → DOP. Convierte importes y permite exportar hasta 50 lecturas de la sesión. No necesita MySQL. La interfaz se adapta mediante componentes nativos de Streamlit.

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

## Despliegue en alwaysdata

```sh
cd ~/apps
git clone https://github.com/Jeison-Rosario/app-dolar.git
cd app-dolar
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
```

Crear un sitio de tipo **programa definido por el usuario / comando personalizado** que ejecute el servidor HTTP de Streamlit (no WSGI). Dirección `bookapp.alwaysdata.net/app-dolar`, directorio de trabajo relativo **`apps/app-dolar`**, comando **`/home/bookapp/apps/app-dolar/.venv/bin/python /home/bookapp/apps/app-dolar/server.py`**, variable **`BASE_PATH=/app-dolar`**. **Desactivar Trim path/recortar ruta**, pues Streamlit gestiona el prefijo de forma nativa. No sobrescribir IP, HOST ni PORT. Mantener las protecciones CORS y XSRF predeterminadas. El proxy debe admitir WebSockets.

Comprobar `/app-dolar/` y `/app-dolar/_stcore/health`, conversión USD/DOP y EUR/DOP, intercambio de monedas, CSV y funcionamiento con dos sesiones. El propietario confirmó el despliegue funcional y las conversiones después de corregir la lectura del campo `rates` del proveedor. Vigilar RAM: Streamlit y pandas pueden consumir más memoria que los proyectos Node. Que el panel permita otro sitio no garantiza capacidad para cuatro aplicaciones. Si aparecen fallos, detener solo el nuevo sitio y revisar el consumo. No se ha contratado ningún plan adicional.

## Estructura

`app.py`: interfaz; `rates.py`: validación, caché y recuperación; `server.py`: arranque; `test_rates.py`: pruebas sin consultas externas ni mensajes; `.env.example`: configuración no sensible.

Versiones comprobadas en Python 3.12: `requirements.lock.txt`. Para reproducirlas usar `pip install -r requirements.lock.txt`; `requirements.txt` mantiene los rangos compatibles para otras versiones de Python.

## Conversión entre monedas

Una sola consulta obtiene todas las tasas respecto a USD. Se calcula `importe × tasa_destino / tasa_origen`; cambiar el par no hace una petición adicional. Solo se ofrecen códigos presentes en la respuesta válida del proveedor (por ejemplo USD, DOP, EUR, MXN y COP, según disponibilidad). Se rechazan tasas no finitas, cero, negativas y respuestas cuya base USD no sea 1.

Las lecturas están limitadas a 50 en total por sesión; el gráfico filtra el par actual para evitar mezclar escalas. El CSV incluye origen, destino, tasa, hora de lectura y actualización del proveedor. Una conversión a la misma moneda conserva el importe. No se incluyen comisiones ni tasas bancarias.
## Demo y recorrido

**[Abrir Conversor de divisas](https://bookapp.alwaysdata.net/app-dolar/)**

1. Elegir moneda de origen y destino; comienza en USD → DOP.
2. Introducir un importe entre 0 y 1000000000 en la moneda de origen.
3. Revisar la tasa, la conversión y las fechas UTC.
4. Utilizar **Intercambiar monedas** para invertir el par, conservando el importe escrito.
5. Descargar las lecturas CSV de la sesión.

El refresco de pantalla opcional no aumenta la frecuencia de actualización del proveedor. **Consultar** usa la caché; no fuerza una llamada externa. Las lecturas se limitan a una por minuto y par, con hasta 50 registros entre todos los pares de una sesión. El gráfico filtra el par actual.

## Integración y configuración

`rates.py` consulta `https://open.er-api.com/v6/latest/USD` y exige `result=success`, base USD y un objeto `rates` con valores positivos finitos y USD=1. No utiliza el campo `conversion_rates`. `RateCache` usa un bloqueo compartido para evitar consultas duplicadas dentro del mismo proceso.

| Variable | Predeterminado | Función |
| --- | --- | --- |
| `BASE_PATH` | vacío | Prefijo nativo de Streamlit |
| `PORT` | `8501` | Puerto |
| `IP` / `HOST` | `127.0.0.1` | Dirección asignada al proceso |

`server.py` carga `.env` sin sobrescribir variables del proceso. En alwaysdata se puede introducir el prefijo en el propio comando:

```sh
env BASE_PATH=/app-dolar /home/bookapp/apps/app-dolar/.venv/bin/python /home/bookapp/apps/app-dolar/server.py
```

Usar tipo **User program**, directorio relativo `apps/app-dolar` y **Trim path desactivado**. Conservar las protecciones CORS/XSRF. El endpoint `/app-dolar/_stcore/health` confirma Streamlit, pero no una consulta exitosa al proveedor.

## Errores y conservación de datos

Si la consulta falla, se espera un minuto antes de reintentar. Si existe una tasa anterior en memoria, se muestra con aviso; si no, se muestra proveedor no disponible. El dato anterior no se guarda en disco. Un reinicio elimina la caché y las lecturas de las sesiones que se pierdan.

| Problema | Comprobación |
| --- | --- |
| `No module named dotenv` | Instalar `requirements.txt` con el Python de `.venv` |
| `Ran 0 tests` | Actualizar el código y ejecutar `-m unittest -v test_rates test_ui` |
| `Not Found` | Revisar barra final, `BASE_PATH` y Trim path |
| Proveedor no disponible | Revisar conexión, HTTP y formato `rates`; no asumir caída por un solo error |
| El gráfico no cambia | Las tasas de referencia son diarias, no cotizaciones en tiempo real |

## Pruebas y alcance

```sh
.venv/bin/python -m unittest -v test_rates test_ui
```

La suite cubre conversiones cruzadas, misma moneda, importes inválidos, respuestas malformadas, caché, espera tras errores, configuración y selectores/intercambio mediante Streamlit AppTest. Usa datos simulados, sin enviar mensajes de Telegram. En Windows utilizar `.venv\Scripts\python.exe`.

No se incluye una integración activa de Telegram en el código actual. Los secretos de versiones antiguas deben revocarse en su servicio; eliminarlos del archivo actual no borra el historial. Las pruebas anteriores fueron verificadas durante la preparación y por el propietario en el servidor; esta ampliación solo modifica documentación.

## Autor

[Jeison Rosario](https://github.com/Jeison-Rosario)
