"""Public USD/DOP demo. Does not send Telegram messages."""
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from rates import RateCache, RateError

st.set_page_config(page_title="Monitor USD/DOP | Jeison Rosario", page_icon="💱", layout="centered")

@st.cache_resource
def shared_rates():
    return RateCache()

st.caption("JEISON ROSARIO · PYTHON + STREAMLIT")
st.title("Monitor USD → DOP")
st.write("Consulta una tasa de referencia y convierte dólares estadounidenses a pesos dominicanos.")
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
    st.metric("DOP por 1 USD", f"RD$ {snapshot.rate:,.4f}")
    st.caption("Actualización del proveedor (UTC): " + snapshot.updated.strftime("%Y-%m-%d %H:%M"))
    st.caption("Última consulta exitosa (UTC): " + snapshot.fetched.strftime("%Y-%m-%d %H:%M"))
    amount = st.number_input("Cantidad en USD", min_value=0.0, max_value=1_000_000_000.0, value=100.0, step=10.0)
    st.success(f"{amount:,.2f} USD ≈ RD$ {amount * snapshot.rate:,.2f}")
    history = st.session_state.setdefault("readings", [])
    minute = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    if not history or history[-1]["Hora UTC"] != minute:
        history.append({"Hora UTC": minute, "DOP por USD": snapshot.rate})
        del history[:-50]
    st.subheader("Lecturas de esta sesión")
    st.caption("Máximo 50 observaciones. No es un historial de movimientos del mercado; varias lecturas pueden tener la misma tasa.")
    frame = pd.DataFrame(history).set_index("Hora UTC")
    st.line_chart(frame)
    st.download_button("Descargar lecturas CSV", frame.to_csv().encode("utf-8"), "lecturas-usd-dop.csv", "text/csv")

dashboard()
st.markdown("[Rates By Exchange Rate API](https://www.exchangerate-api.com)")
st.caption("Demo sin base de datos. Las lecturas desaparecen al reiniciar la sesión. Los avisos de Telegram están desactivados.")
