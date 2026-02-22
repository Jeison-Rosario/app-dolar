import streamlit as st
import requests
import time
import pandas as pd
import os
from datetime import datetime

# =========================
# CONFIG
# =========================

EXCHANGE_URL = "https://api.frankfurter.app/latest?from=USD&to=DOP"

BOT_TOKEN = "8279723703:AAGpbxC7gRPbUrWEV7WMMC5GmVOL2eV5NOA"  # 🔐 Variable de entorno
CHAT_IDS = ["1180916427", "6158759375"]

threshold = 60
interval = 10

headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# FUNCIONES
# =========================

def get_usd_dop():
    try:
        response = requests.get(EXCHANGE_URL, headers=headers, timeout=5)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        if not response.text:
            raise Exception("Respuesta vacía de la API")

        data = response.json()

        if "rates" not in data or "DOP" not in data["rates"]:
            raise Exception("Formato inesperado de API")

        return float(data["rates"]["DOP"])

    except Exception as e:
        st.error(f"Error obteniendo tasa: {e}")
        return None


def send_telegram_alert(message):
    if not BOT_TOKEN:
        st.warning("BOT_TOKEN no configurado en variables de entorno")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            response = requests.post(url, data=payload, timeout=5)

            if response.status_code != 200:
                st.warning(f"Error enviando a chat {chat_id}")

        except Exception as e:
            st.warning(f"Error Telegram: {e}")

# =========================
# INTERFAZ
# =========================

st.title("📊 Monitor USD → DOP en Tiempo Real")

if "data" not in st.session_state:
    st.session_state.data = []

if "alert_sent" not in st.session_state:
    st.session_state.alert_sent = False

rate = get_usd_dop()

# Si falla la API no rompemos la app
if rate is None:
    st.stop()

now = datetime.now()

# Guardar histórico
st.session_state.data.append({"time": now, "rate": rate})

# Limitar historial
if len(st.session_state.data) > 50:
    st.session_state.data.pop(0)

df = pd.DataFrame(st.session_state.data)

# Gráfico
st.line_chart(df.set_index("time"))

# Métrica actual
st.metric("Precio actual USD/DOP", f"RD${rate:.2f}")

# =========================
# ALERTA
# =========================

if rate > threshold and not st.session_state.alert_sent:
    st.warning("🚨 El dólar superó el umbral")
    send_telegram_alert(
        f"🚨 ALERTA 🚨\nUSD superó RD${threshold}\nValor actual: RD${rate:.2f}"
    )
    st.session_state.alert_sent = True

if rate <= threshold:
    st.session_state.alert_sent = False

# =========================
# AUTO REFRESH
# =========================

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > interval:
    st.session_state.last_refresh = time.time()
    st.rerun()