import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import yfinance as yf
import requests
import json
import os
from modules.market_data import get_all_prices, is_market_open
from modules.gold_api import get_gold_price, get_silver_price

st.set_page_config(page_title="Taoussi Trader", layout="wide")

# Style personnalisé
st.markdown("""
<style>
    body { background-color: #0a0a0a; color: white; }
    .stApp { background-color: #0a0a0a; }
    .css-18e3th9 { background-color: #0a0a0a; }
    .css-1d391kg { background-color: #0a0a0a; }
</style>
""", unsafe_allow_html=True)

st.title("📊 TAOUSSI TRADER · Bourse de Casa")
st.caption(f"Heure Maroc : {datetime.now(pytz.timezone('Africa/Casablanca')).strftime('%H:%M:%S')}")

# Statut marché
col1, col2, col3 = st.columns(3)
if is_market_open():
    col1.success("📈 Marché OUVERT (données live)")
else:
    col1.warning("⏸️ Marché FERMÉ (données cache)")

# Métaux précieux
try:
    gold, gold_var = get_gold_price()
    silver, silver_var = get_silver_price()
    col2.metric("Or (USD)", f"${gold:,.2f}", f"{gold_var:+.2f}%")
    col3.metric("Argent (USD)", f"${silver:,.2f}", f"{silver_var:+.2f}%")
except Exception as e:
    col2.error(f"GoldAPI erreur: {str(e)[:50]}")

# Actions Casa
st.subheader("🇲🇦 Actions Maroc")
prices = get_all_prices()

if prices:
    df = pd.DataFrame([
        {"Symbole": sym, "Prix (DH)": f"{prix:,.2f}" if prix else "N/A"}
        for sym, prix in prices.items() if prix
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("Aucune donnée disponible pour les actions")

# Footer
st.markdown("---")
st.caption("Données via yfinance · Or/Argent via GoldAPI · Mise à jour automatique")
