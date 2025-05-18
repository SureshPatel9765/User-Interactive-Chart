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

# Open your sheet
sheet = client.open("Pydroid 3 Projects")
data_sheet = sheet.worksheet("Data")

# === Load NSE symbols ===
# For demonstration, using a predefined list. Replace this with actual data loading as needed.
tickers = ["INFY", "TCS", "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "WIPRO", "HCLTECH", "ITC", "LT", "AXISBANK"]

# === User Input ===
st.title("📈 NSE Stock Analysis")

# Text input for custom symbol
user_input = st.text_input("Enter NSE symbol (e.g., TCS):").upper().strip()

# Dropdown for predefined symbols
selected_dropdown = st.selectbox("Or select from popular NSE stocks:", tickers)

# Determine the selected symbol
selected = user_input if user_input else selected_dropdown
if selected_dropdown:
        user_input=" "
  
full_symbol = (
        f'=GOOGLEFINANCE("NSE:{selected}",'
        '"all",TODAY()-250,TODAY())'
)
# Update the ticker in Google Sheets
data_sheet.update_acell("A1", full_symbol)
st.write(f"✅ Updated ticker in Data:A1 formula to **{full_symbol}**, fetching new data…")
time.sleep(5)  # Wait for data to be fetched via GoogleFinance formula

# Fetch data from the sheet
data = data_sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    if "Date" in df.columns and "Close" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Close"] = pd.to_numeric(df["Close"], errors='coerce')

        # Calculate EMA and RSI
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

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

        # Plot Price and EMA
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Close"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["EMA_20"], mode="lines", name="EMA 20"))

        # Dynamic Y-axis range
        y_min = df["Close"].min()
        y_max = df["Close"].max()
        y_range = [y_min - (y_max - y_min) * 0.1, y_max + (y_max - y_min) * 0.1]

        fig.update_layout(
            title=f"{selected} Price Chart with EMA",
            xaxis_title="Date",
            yaxis_title="Price",
            yaxis=dict(range=y_range)
        )

        st.plotly_chart(fig)

        # Plot RSI
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], mode="lines", name="RSI"))
        fig_rsi.update_layout(
            title=f"{selected} RSI",
            xaxis_title="Date",
            yaxis_title="RSI",
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig_rsi)

    else:
        st.write("Required columns not found in the sheet.")
else:
    st.write("No data available.")

# === Display Available Symbols ===
with st.expander("📘 View Available NSE Symbols"):
    st.write(", ".join(tickers))
