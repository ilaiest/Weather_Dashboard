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

# 🔹 Función para Cargar Datos de Google Sheets
@st.cache_data
def load_google_sheets():
    """Carga todos los datos desde Google Sheets para optimización."""
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        weather_df = pd.DataFrame(data[1:], columns=data[0])

        # Convertir tipos de datos
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        numeric_cols = ["temp", "feels_like", "wind_speed", "humidity"]
        for col in numeric_cols:
            weather_df[col] = pd.to_numeric(weather_df[col], errors="coerce")

        # Cargar datos de equipos y clusters
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
    
    # Filtrar por fecha
    weather_df = weather_df[weather_df["date"] == selected_date]

    # Merge con team_df para agregar cluster y team
    if not team_df.empty:
        weather_df = weather_df.merge(team_df, on="city", how="left")
    
    # Mostrar columnas después del merge para depuración
    st.write("Columnas después del merge:", weather_df.columns.tolist())

    # Verificar si 'team' y 'cluster' existen antes de filtrar
    if "team" in weather_df.columns and selected_team != "All":
        weather_df = weather_df[weather_df["team"] == selected_team]

    if "cluster" in weather_df.columns and selected_cluster != "All":
        weather_df = weather_df[weather_df["cluster"] == selected_cluster]
    
    return weather_df

# 🚀 Sidebar: View Selection
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 Filtros
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today()).strftime("%Y-%m-%d")
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster", ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 **City Overview**
if page == "🌍 City Overview":
    st.markdown(f"## 🌍 Weather Overview for {selected_date}")

    weather_df = fetch_weather_data(selected_date, selected_team, selected_cluster)

    if not weather_df.empty:
        st.write("Vista previa de datos filtrados:", weather_df.head())  # ✅ Mostrar datos después del filtro

        cols = st.columns(3)  # 3 ciudades por fila
        for idx, row in weather_df.iterrows():
            weather_icon = "🌎"
            with cols[idx % 3]:
                st.markdown(f"""
                    <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white;">
                        <h3>{weather_icon} {row['city']}</h3>
                        <p>🌡️ Temperature: {row['temp']}°C | Feels Like: {row['feels_like']}°C</p>
                        <p>🌬️ Wind Speed: {row['wind_speed']} km/h</p>
                        <p>💧 Humidity: {row['humidity']}%</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No weather data available for the selected filters.")
