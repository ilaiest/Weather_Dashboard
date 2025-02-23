import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# 🚀 **Debe ser la primera línea de Streamlit**
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# 🔹 Configuración de Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 Cargar credenciales desde `st.secrets`
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Weather_Dashboard")
    st.success("✅ Conexión exitosa con Google Sheets.")
except Exception as e:
    st.error(f"❌ Error al autenticar con Google Sheets: {e}")
    st.stop()

# 🔹 Diccionario de Iconos de Clima
weather_icons = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Drizzle": "🌦️",
    "Rain": "🌧️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌁"
}

# 🔹 Función para Cargar Datos de Google Sheets
@st.cache_data
def load_google_sheets():
    """Carga todos los datos desde Google Sheets para optimización."""
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        weather_df = pd.DataFrame(data[1:], columns=data[0])

        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        weather_df["temp"] = pd.to_numeric(weather_df["temp"], errors="coerce")
        weather_df["feels_like"] = pd.to_numeric(weather_df["feels_like"], errors="coerce")
        weather_df["wind_speed"] = pd.to_numeric(weather_df["wind_speed"], errors="coerce")
        weather_df["humidity"] = pd.to_numeric(weather_df["humidity"], errors="coerce")

        team_worksheet = spreadsheet.worksheet("City_Team_Cluster")
        team_data = team_worksheet.get_all_values()
        team_df = pd.DataFrame(team_data[1:], columns=team_data[0])

        return weather_df, team_df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 🔹 Función para obtener datos de clima filtrados
def fetch_weather_data(selected_date, selected_team, selected_cluster):
    weather_df, team_df = load_google_sheets()
    weather_df = weather_df[weather_df["date"] == selected_date]

    if selected_team != "All":
        weather_df = weather_df.merge(team_df, on="city", how="left")
        weather_df = weather_df[weather_df["team"] == selected_team]
    if selected_cluster != "All":
        weather_df = weather_df[weather_df["cluster"] == selected_cluster]

    return weather_df

# 🔹 Función para obtener pronóstico por ciudad
def fetch_city_forecast(city):
    weather_df, _ = load_google_sheets()
    return weather_df[weather_df["city"] == city]

# 🔹 Sidebar: Filtros y Navegación
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 Filtros
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today().date())
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster", ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 SECCIÓN 1: City Overview
if page == "🌍 City Overview":
    st.markdown(f"<h2 style='color:#00AEEF;'>🌎 Weather Overview for {selected_date}</h2>", unsafe_allow_html=True)

    weather_df = fetch_weather_data(selected_date, selected_team, selected_cluster)

    if not weather_df.empty:
        num_cols = 3
        rows = [weather_df.iloc[i:i + num_cols] for i in range(0, len(weather_df), num_cols)]

        for row in rows:
            cols = st.columns(num_cols)
            for idx, (col, row_data) in enumerate(zip(cols, row.itertuples())):
                weather_icon = weather_icons.get(row_data.main_condition, "🌍")
                with col:
                    st.markdown(
                        f"""
                        <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; margin-bottom: 10px;">
                            <h3 style="color: #00AEEF;">{weather_icon} {row_data.city}</h3>
                            <p>🌡️ <strong>Temperature:</strong> {row_data.temp}°C (Feels Like: {row_data.feels_like}°C)</p>
                            <p>🌬️ <strong>Wind Speed:</strong> {row_data.wind_speed} km/h</p>
                            <p>💧 <strong>Humidity:</strong> {row_data.humidity}%</p>
                        </div>
                        """, unsafe_allow_html=True
                    )
        cols = st.columns(3)  # Mostrar en 3 columnas
        for idx, row in weather_df.iterrows():
            weather_icon = weather_icons.get(row['weather_condition'], "🌎")  
            with cols[idx % 3]:  
                st.markdown(
                    f"""
                    <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white;">
                        <h3>{weather_icon} {row['city']}</h3>
                        <p>🌡️ Temperature: {row['temp']}°C | Feels Like: {row['feels_like']}°C</p>
                        <p>🌬️ Wind Speed: {row['wind_speed']} km/h</p>
                        <p>💧 Humidity: {row['humidity']}%</p>
                    </div>
                    """, unsafe_allow_html=True
                )
    else:
        st.warning("No weather data available for the selected filters.")

@@ -127,14 +123,13 @@

        if not city_forecast_df.empty:
            today_weather = city_forecast_df.iloc[0]
            weather_icon = weather_icons.get(today_weather["weather_condition"].strip().lower(), "🌎")
            weather_icon = weather_icons.get(today_weather["weather_condition"], "🌎")

            st.markdown(f"""
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; text-align: center;">
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white;">
                    <h2 style="color: #00AEEF;">{selected_city} - {today_weather['date']}</h2>
                    <h1 style="font-size: 60px;">{weather_icon} {today_weather['temp']}°C</h1>
                    <p style="font-size: 20px;">Feels Like: {today_weather['feels_like']}°C</p>
                    <p style="font-size: 18px;">{today_weather['weather_condition']}</p>
                </div>
            """, unsafe_allow_html=True)
