import streamlit as st
import pandas as pd
import gspread
import json
import os
from google.oauth2 import service_account
from datetime import datetime
import plotly.express as px

import streamlit as st
import pandas as pd
import gspread
import json
import os
from google.oauth2 import service_account
from datetime import datetime
import plotly.express as px

# 🔹 Definir los permisos correctos para Google Sheets
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]

# 🔹 Cargar credenciales desde Streamlit Secrets
try:
    GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
    creds_dict = json.loads(GOOGLE_CREDENTIALS)

    # Crear credenciales con los permisos correctos (scope)
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    
    # Autenticación con Google Sheets
    client = gspread.authorize(creds)
    spreadsheet = client.open("Weather_Dashboard")

except json.JSONDecodeError:
    st.error("❌ Error al leer las credenciales. Verifica el formato en Streamlit Secrets.")
    st.stop()
except gspread.exceptions.APIError:
    st.error("❌ No se pudo conectar con Google Sheets. Verifica permisos y acceso al archivo.")
    st.stop()
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

# 🔹 Función para Cargar Datos de Google Sheets con Caché
@st.cache_data
def load_google_sheets():
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        weather_df = pd.DataFrame(data[1:], columns=data[0])

        # Convertir columnas a los tipos adecuados
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        weather_df["temp"] = pd.to_numeric(weather_df["temp"], errors="coerce")
        weather_df["feels_like"] = pd.to_numeric(weather_df["feels_like"], errors="coerce")
        weather_df["wind_speed"] = pd.to_numeric(weather_df["wind_speed"], errors="coerce")
        weather_df["humidity"] = pd.to_numeric(weather_df["humidity"], errors="coerce")

        # Cargar la hoja "City_Team_Cluster"
        team_worksheet = spreadsheet.worksheet("City_Team_Cluster")
        team_data = team_worksheet.get_all_values()
        team_df = pd.DataFrame(team_data[1:], columns=team_data[0])

        return weather_df, team_df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 🔹 Función para obtener datos del clima
def fetch_weather_data(selected_date, selected_team, selected_cluster):
    weather_df, team_df = load_google_sheets()
    weather_df = weather_df[weather_df["date"] == selected_date]

    if selected_team != "All":
        weather_df = weather_df.merge(team_df, on="city", how="left")
        weather_df = weather_df[weather_df["team"] == selected_team]
    if selected_cluster != "All":
        weather_df = weather_df[weather_df["cluster"] == selected_cluster]

    return weather_df

# 🔹 Función para obtener pronóstico de una ciudad
def fetch_city_forecast(city):
    weather_df, _ = load_google_sheets()
    return weather_df[weather_df["city"] == city]

# 🚀 Configuración de Streamlit
st.set_page_config(page_title="Weather Dashboard", layout="wide")

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
                        <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white;">
                            <h3 style="color: #00AEEF;">{weather_icon} {row_data.city}</h3>
                            <p>🌤️ <strong>Weather Condition:</strong> {row_data.weather_condition}</p>
                            <p>🌡️ <strong>Temperature:</strong> {row_data.temp}°C <span style="color: #FFA500;">(Feels Like: {row_data.feels_like}°C)</span></p>
                            <p>🌬️ <strong>Wind Speed:</strong> {row_data.wind_speed} km/h</p>
                            <p>💧 <strong>Humidity:</strong> {row_data.humidity}%</p>
                            <p>🌧️ <strong>Rain Probability:</strong> {row_data.rain_probability}</p>
                        </div>
                        """, unsafe_allow_html=True
                    )
    else:
        st.warning("No weather data available for the selected filters.")

# 📊 SECCIÓN 2: Detailed Forecast
elif page == "📊 Detailed Forecast":
    st.markdown("## 📊 5-Day Forecast")
    city_list = ["Select a City"] + fetch_weather_data(selected_date, selected_team, selected_cluster)["city"].unique().tolist()
    selected_city = st.selectbox("🏙️ Choose a City", city_list)

    if selected_city != "Select a City":
        city_forecast_df = fetch_city_forecast(selected_city)
        if not city_forecast_df.empty:
            today_weather = city_forecast_df.iloc[0]
            weather_icon = weather_icons.get(today_weather["weather_condition"], "🌎")
            st.markdown(f"""
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; text-align: center;">
                    <h2 style="color: #00AEEF;">{selected_city} - {today_weather['date']}</h2>
                    <h1>{weather_icon} {today_weather['temp']}°C</h1>
                    <p>Feels Like: {today_weather['feels_like']}°C</p>
                    <p>🌬️ Wind Speed: {today_weather['wind_speed']} km/h | 💧 Humidity: {today_weather['humidity']}%</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### 📈 Temperature Trends")
            fig_temp = px.line(city_forecast_df, x="date", y=["temp", "feels_like"], title="🌡️ Temperature Over the Next Days", markers=True)
            st.plotly_chart(fig_temp, use_container_width=True)

            st.markdown("### 🌧️ Rain Probability Trend")
            fig_rain = px.bar(city_forecast_df, x="date", y="rain_probability", title="🌧️ Rain Probability Over the Next Days", text="rain_probability")
            st.plotly_chart(fig_rain, use_container_width=True)
        else:
            st.warning("No forecast data available for this city.")
