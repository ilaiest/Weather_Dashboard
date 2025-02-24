import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Weather Dashboard", layout="wide")

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 **Diccionario de Iconos de Clima**
weather_icons = {
    "clear sky": "☀️",
    "few clouds": "🌤️",
    "scattered clouds": "⛅",
    "broken clouds": "☁️",
    "overcast clouds": "🌥️",
    "drizzle": "🌦️",
    "light rain": "🌦️",
    "moderate rain": "🌧️",
    "heavy rain": "🌧️",
    "thunderstorm": "⛈️",
    "snow": "❄️",
    "mist": "🌫️",
    "fog": "🌫️",
    "haze": "🌁",
    "smoke": "🌫️",
    "dust": "💨",
    "sand": "💨",
    "volcanic ash": "🌋",
    "squalls": "🌬️",
    "tornado": "🌪️"
}

# 🔹 **Autenticación con Google Sheets**
try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Weather_Dashboard")
except Exception as e:
    st.error(f"❌ Error al autenticar con Google Sheets: {e}")
    st.stop()

# 🔹 **Función para Cargar Datos de Google Sheets**
@st.cache_data
def load_google_sheets():
    """Carga datos de Google Sheets con validaciones."""
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        if not data:
            st.error("⚠️ No se encontraron datos en la hoja 'Data'.")
            return pd.DataFrame(), pd.DataFrame()

        weather_df = pd.DataFrame(data[1:], columns=data[0])

        # Convertir tipos de datos
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        numeric_cols = ["temp", "feels_like", "wind_speed", "humidity", "rain_probability", "rain_hours"]
        for col in numeric_cols:
            weather_df[col] = pd.to_numeric(weather_df[col], errors="coerce")

        # Cargar datos de equipos y clusters
        team_worksheet = spreadsheet.worksheet("City_Team_Cluster")
        team_data = team_worksheet.get_all_values()
        
        team_df = pd.DataFrame(team_data[1:], columns=team_data[0]) if team_data else pd.DataFrame()

        return weather_df, team_df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 🔹 **Función para obtener datos de clima filtrados**
def fetch_weather_data(selected_date, selected_team, selected_cluster):
    weather_df, team_df = load_google_sheets()

    # Validación si no hay datos
    if weather_df.empty:
        return pd.DataFrame()

    # Filtrar por fecha
    weather_df = weather_df[weather_df["date"] == selected_date]

    # Merge con team_df si tiene datos
    if not team_df.empty and "city" in weather_df.columns and "city" in team_df.columns:
        weather_df = weather_df.merge(team_df, on="city", how="left")

    # ✅ Manejo de valores NaN y espacios en blanco en 'cluster'
    if "cluster" in weather_df.columns:
        weather_df["cluster"] = weather_df["cluster"].fillna("Unknown").astype(str).str.strip()
    
    selected_cluster = selected_cluster.strip()

    # ✅ Filtrar por 'team' si existe la columna
    if "team" in weather_df.columns and selected_team != "All":
        weather_df = weather_df[weather_df["team"] == selected_team]

    # ✅ Filtrar por 'cluster' si existe en los datos
    if "cluster" in weather_df.columns and selected_cluster != "All":
        if selected_cluster in weather_df["cluster"].unique():
            weather_df = weather_df[weather_df["cluster"] == selected_cluster]
        else:
            st.warning(f"No hay datos para el cluster '{selected_cluster}'. Mostrando todos los datos.")

    return weather_df

# 🚀 **Sidebar: Selección de Vista**
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 **Filtros**
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today().date())
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster", ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 **City Overview**
if page == "🌍 City Overview":
    st.markdown(f"## 🌍 Weather Overview for {selected_date}")

    weather_df = fetch_weather_data(selected_date, selected_team, selected_cluster)

    if not weather_df.empty:
        cols = st.columns(min(3, len(weather_df)))  # Ajusta a máximo 3 columnas o menos si hay menos ciudades
        for idx, row in weather_df.iterrows():
            weather_icon = weather_icons.get(row['weather_condition'], "🌎")
            with cols[idx % len(cols)]:  # Evita errores de índice si hay menos de 3 ciudades
                st.markdown(
                    f"""
                    <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; margin-bottom: 10px;">
                        <h3>{weather_icon} {row['city']}</h3>
                        <p>🌡️ Temperature: {row['temp']}°C | Feels Like: {row['feels_like']}°C</p>
                        <p>🌬️ Wind Speed: {row['wind_speed']} km/h</p>
                        <p>💧 Humidity: {row['humidity']}%</p>
                        <p>🌧️ Rain Probability: {row['rain_probability']}%</p>
                        <p>⏳ Rain Hours: {row['rain_hours'] if row['rain_hours'] else 'No Rain Expected'}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
    else:
        st.warning("⚠️ No weather data available for the selected filters.")
