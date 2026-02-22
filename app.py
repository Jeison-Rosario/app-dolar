import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# CONFIG
EXCHANGE_URL = "https://cdn.moneyconvert.net/api/latest.json"
BOT_TOKEN = "8279723703:AAGpbxC7gRPbUrWEV7WMMC5GmVOL2eV5NOA"
CHAT_IDS = ["1180916427", "6158759375"]  # Lista correcta

threshold = 60
interval = 10  # segundos

# =========================
# FUNCIONES
# =========================

def get_usd_dop():
    response = requests.get(EXCHANGE_URL, timeout=5)
    data = response.json()
    return float(data["rates"]["DOP"])

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        requests.post(url, data=payload)

# =========================
# INTERFAZ
# =========================

st.title("📊 Monitor USD → DOP en Tiempo Real")

if "data" not in st.session_state:
    st.session_state.data = []

if "alert_sent" not in st.session_state:
    st.session_state.alert_sent = False

# Obtener precio
rate = get_usd_dop()
now = datetime.now()

# Guardar histórico
st.session_state.data.append({"time": now, "rate": rate})

# Limitar a últimos 50 registros
if len(st.session_state.data) > 50:
    st.session_state.data.pop(0)

df = pd.DataFrame(st.session_state.data)

# Mostrar gráfico
st.line_chart(df.set_index("time"))

# Mostrar precio actual
st.metric("Precio actual USD/DOP", f"RD${rate:.2f}")

# Alerta
if rate > threshold and not st.session_state.alert_sent:
    st.warning("🚨 El dólar superó el umbral")
    send_telegram_alert(f"🚨 ALERTA 🚨\nUSD superó RD${threshold}\nValor actual: RD${rate:.2f}")
    st.session_state.alert_sent = True

# Reiniciar alerta si baja
if rate <= threshold:
    st.session_state.alert_sent = False

# =========================
# AUTO REFRESH
# =========================

# Configurar un temporizador para el auto-refresh
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Verificar si ha pasado el intervalo
if time.time() - st.session_state.last_refresh > interval:
    st.session_state.last_refresh = time.time()
    st.rerun()