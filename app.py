"""Public multi-currency demo. Does not send Telegram messages."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from rates import RateCache, RateError, cross_rate, convert

st.set_page_config(page_title="Conversor de divisas | Jeison Rosario", page_icon="💱", layout="centered")

@st.cache_resource
def shared_rates():
    return RateCache()

st.caption("JEISON ROSARIO · PYTHON + STREAMLIT")
st.title("Conversor de divisas")
st.write("Elige tus monedas de origen y destino para consultar una conversión de referencia.")
st.info("El proveedor gratuito actualiza sus tasas una vez al día. Esta referencia no representa la tasa de compra o venta de un banco.")
auto = st.checkbox("Actualizar la pantalla cada minuto", value=False)

@st.fragment(run_every=60 if auto else None)
def dashboard():
    st.button("Consultar", help="Utiliza la caché compartida; no fuerza una consulta externa.")
    try:
        snapshot = shared_rates().get()
    except RateError as exc:
        st.error(str(exc))
        return
    if snapshot.stale:
        st.warning("El proveedor no respondió. Se muestra la última tasa disponible en memoria.")
    codes = sorted(snapshot.rates)
    defaults = {"source": "USD", "target": "DOP"}
    for key, default in defaults.items():
        if st.session_state.get(key) not in codes:
            st.session_state[key] = default if default in codes else codes[0]

    def swap():
        st.session_state.source, st.session_state.target = st.session_state.target, st.session_state.source

    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Moneda de origen", codes, key="source")
    with col2:
        target = st.selectbox("Moneda de destino", codes, key="target")
    st.button("Intercambiar monedas", on_click=swap)
    rate = cross_rate(snapshot, source, target)
    st.metric(f"{target} por 1 {source}", f"{rate:,.6f}")
    st.caption("Actualización del proveedor (UTC): " + snapshot.updated.strftime("%Y-%m-%d %H:%M"))
    st.caption("Última consulta exitosa (UTC): " + snapshot.fetched.strftime("%Y-%m-%d %H:%M"))
    amount = st.number_input("Importe en moneda de origen", min_value=0.0, max_value=1_000_000_000.0, value=100.0, step=10.0)
    st.success(f"{amount:,.2f} {source} ≈ {convert(snapshot, amount, source, target):,.2f} {target}")
    history = st.session_state.setdefault("readings_multi", [])
    minute = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    if not any(r["Hora UTC"] == minute and r["Origen"] == source and r["Destino"] == target for r in history):
        history.append({"Hora UTC": minute, "Origen": source, "Destino": target, "Tasa": rate,
                        "Actualización proveedor UTC": snapshot.updated.isoformat()})
        del history[:-50]
    st.subheader("Lecturas de esta sesión")
    st.caption("Máximo 50 observaciones entre todos los pares. El gráfico muestra solo el par seleccionado; no es un historial del mercado.")
    pair = [r for r in history if r["Origen"] == source and r["Destino"] == target]
    if pair:
        st.line_chart(pd.DataFrame(pair).set_index("Hora UTC")[["Tasa"]])
    frame = pd.DataFrame(history)
    st.download_button("Descargar lecturas CSV", frame.to_csv(index=False).encode("utf-8"), "lecturas-divisas.csv", "text/csv")

dashboard()
st.markdown("[Rates By Exchange Rate API](https://www.exchangerate-api.com)")
st.caption("Demo sin base de datos. Las lecturas desaparecen al reiniciar la sesión. Los avisos de Telegram están desactivados.")
