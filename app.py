import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import plotly.graph_objects as go

# === Setup Google Sheets access ===
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets.gcp_service_account, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open("Pydroid 3 Projects")
data_sheet = sheet.worksheet("Data")

# === Load predefined NSE symbols ===
tickers = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "WIPRO", "HCLTECH", "ITC", "LT", "AXISBANK"]

# === UI Layout ===
st.title("📈 NSE Stock Analysis")

# Input section

user_input = st.text_input("Enter NSE symbol (e.g., TCS):").upper().strip()
selected_dropdown = st.selectbox("Or select from popular NSE stocks:", tickers)
# Use typed input if available, otherwise dropdown
selected = user_input if user_input else selected_dropdown

# === GoogleFinance Formula & Update ===
full_symbol = f'=GOOGLEFINANCE("NSE:{selected}","all",TODAY()-250,TODAY())'
user_input=" "
try:
    data_sheet.update_acell("A1", full_symbol)
    st.success(f"✅ Updated ticker formula in A1 to fetch: {selected}")
    time.sleep(5)
except Exception as e:
    st.error(f"Failed to update Google Sheet: {e}")

# === Read Sheet Data ===
data = data_sheet.get_all_records()
if not data:
    st.warning("No data returned from the sheet.")
else:
    df = pd.DataFrame(data)
    if "Date" in df.columns and "Close" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Close"] = pd.to_numeric(df["Close"], errors='coerce')
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

        # === RSI Calculation ===
        def compute_rsi(series, window=14):
            delta = series.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        df["RSI"] = compute_rsi(df["Close"])

        # === Display Charts in Tabs ===
        tab1, tab2 = st.tabs(["📊 Price Chart", "📈 RSI Indicator"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Close"))
            fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA_20"], mode="lines", name="EMA 20"))
            y_min, y_max = df["Close"].min(), df["Close"].max()
            fig.update_layout(
                title=f"{selected} Price Chart with EMA",
                xaxis_title="Date",
                yaxis_title="Price",
                yaxis=dict(range=[y_min - (y_max - y_min)*0.1, y_max + (y_max - y_min)*0.1])
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], mode="lines", name="RSI"))
            fig_rsi.update_layout(
                title=f"{selected} RSI",
                xaxis_title="Date",
                yaxis_title="RSI",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
    else:
        st.warning("Required columns 'Date' and 'Close' not found in the sheet.")

# === Show all predefined tickers ===
with st.expander("📘 View Available NSE Symbols"):
    st.write(", ".join(tickers))

