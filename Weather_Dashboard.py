import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px

# 🔹 Configuración de Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
client = gspread.authorize(CREDS)

# Abrir el Google Sheet
spreadsheet = client.open("Weather_Dashboard")

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


# 🔹 Función para Cargar Datos de Google Sheets (Usa Caché para optimización)
@st.cache_data
def load_google_sheets():
    """Carga todos los datos desde Google Sheets una sola vez para evitar múltiples lecturas."""
    try:
        # Cargar la hoja "Data"
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


# 🔹 Nueva función optimizada para obtener datos del clima con la información ya cargada
def fetch_weather_data(selected_date, selected_team, selected_cluster):
    weather_df, team_df = load_google_sheets()

    # Filtrar por fecha
    weather_df = weather_df[weather_df["date"] == selected_date]

    # Filtrar por equipo y cluster si se selecciona uno
    if selected_team != "All":
        weather_df = weather_df.merge(team_df, on="city", how="left")
        weather_df = weather_df[weather_df["team"] == selected_team]
    if selected_cluster != "All":
        weather_df = weather_df[weather_df["cluster"] == selected_cluster]

    return weather_df


# 🔹 Nueva función optimizada para obtener el pronóstico de una ciudad
def fetch_city_forecast(city):
    weather_df, _ = load_google_sheets()
    return weather_df[weather_df["city"] == city]


# 🚀 Configuración de Streamlit
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# 🔹 Sidebar: Filtros y Navegación
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
st.sidebar.markdown("<h4 style='font-size: 22px;'>Select a View:</h4>", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 Filtros
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today().date())
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster", ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 SECCIÓN 1: City Overview (Mejor distribución de las tarjetas)
if page == "🌍 City Overview":
    st.markdown(f"<h2 style='color:#00AEEF;'>🌎 Weather Overview for {selected_date}</h2>", unsafe_allow_html=True)

    weather_df = fetch_weather_data(selected_date, selected_team, selected_cluster)

    if not weather_df.empty:
        num_cols = 3  # Número de columnas por fila
        rows = [weather_df.iloc[i:i + num_cols] for i in range(0, len(weather_df), num_cols)]

        for row in rows:
            cols = st.columns(num_cols)  # Crear columnas dinámicas
            for idx, (col, row_data) in enumerate(zip(cols, row.itertuples())):
                weather_icon = weather_icons.get(row_data.main_condition, "🌍")
                with col:
                    st.markdown(
                        f"""
                        <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; margin-bottom: 10px;">
                            <h3 style="color: #00AEEF;">{weather_icon} {row_data.city}</h3>
                            <p>🌤️ <strong>Weather Condition:</strong> {row_data.weather_condition}</p>
                            <p>🌡️ <strong>Temperature:</strong> {row_data.temp}°C <span style="color: #FFA500;">(Feels Like: {row_data.feels_like}°C)</span></p>
                            <p>🌬️ <strong>Wind Speed:</strong> {row_data.wind_speed} km/h</p>
                            <p>💧 <strong>Humidity:</strong> {row_data.humidity}%</p>
                            <p>🌧️ <strong>Rain Probability:</strong> {row_data.rain_probability}</p>
                            <p>⏳ <strong>Rain Hours:</strong> {row_data.rain_hours if row_data.rain_hours else 'No Rain Expected'}</p>
                        </div>
                        """, unsafe_allow_html=True
                    )
    else:
        st.warning("No weather data available for the selected filters.")


# 📊 SECTION 2: Detailed Forecast (Nueva vista)
elif page == "📊 Detailed Forecast":
    st.markdown("## 📊 5-Day Forecast")

    # Selección de ciudad
    city_list = ["Select a City"] + fetch_weather_data(selected_date, selected_team, selected_cluster)["city"].unique().tolist()
    selected_city = st.selectbox("🏙️ Choose a City", city_list)

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

    if selected_city != "Select a City":
        city_forecast_df = fetch_city_forecast(selected_city)

        if not city_forecast_df.empty:
            # 🔹 Normalizamos la condición climática para asegurar coincidencias con los íconos
            today_weather = city_forecast_df.iloc[0]
            normalized_condition = today_weather["weather_condition"].strip().lower()
            weather_icon = weather_icons.get(normalized_condition, "🌎")  # 🔹 Usa ícono si existe, si no, pone 🌎

            # Tarjeta de clima principal
            st.markdown(f"""
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; text-align: center;">
                    <h2 style="color: #00AEEF;">{selected_city} - {today_weather['date']}</h2>
                    <h1 style="font-size: 60px;">{weather_icon} {today_weather['temp']}°C</h1>
                    <p style="font-size: 20px;">Feels Like: {today_weather['feels_like']}°C</p>
                    <p style="font-size: 18px;">{today_weather['weather_condition']}</p>
                    <p style="font-size: 18px;">🌬️ Wind Speed: {today_weather['wind_speed']} km/h | 💧 Humidity: {today_weather['humidity']}%</p>
                    <p style="font-size: 18px;">🌧️ Rain Probability: {today_weather['rain_probability']} | ⏳ Rain Hours: {today_weather['rain_hours'] if today_weather['rain_hours'] else 'No Rain Expected'}</p>
                </div>
            """, unsafe_allow_html=True)

            # 📅 Forecast de los próximos días (Ajustado para mayor tamaño)
            st.markdown("<h3 style='color:#00AEEF; text-align: center;'>🌤️ 4-Day Weather Forecast</h3>", unsafe_allow_html=True)

            forecast_days = city_forecast_df.iloc[:4]  # 🔹 Tomamos solo los primeros 4 días para evitar errores
            forecast_cols = st.columns(len(forecast_days))  # 🔹 Generamos columnas dinámicas según los días disponibles

            for idx, row in enumerate(forecast_days.itertuples()):  # 🔹 Usamos enumerate para evitar errores de índice
                forecast_icon = weather_icons.get(row.weather_condition, "🌎")  # Obtener icono basado en la condición climática
                with forecast_cols[idx]:  # Ubicar en la columna correspondiente
                    st.markdown(f"""
                <div style="border-radius: 10px; padding: 20px; background-color: #2E2E2E; color: white; text-align: center;
                            width: 150px; height: 160px; margin-left: 50px;">
                    <h4 style="margin: 0; font-size: 20px; margin-bottom: -10px;">{row.date.strftime('%a')}</h4>
                    <p style="font-size: 40px; margin: -10px 0;">{forecast_icon}</p>
                    <h4 style="margin: 0; font-size: 18px; margin-top: -10px;">{row.temp}°C</h4>
                </div>
                    """, unsafe_allow_html=True)

            # 📈 Temperature Trend
            st.markdown("### 📈 Temperature Trends")
            fig_temp = px.line(city_forecast_df, x="date", y=["temp", "feels_like"],
                               labels={"value": "Temperature (°C)", "date": "Date"},
                               title="🌡️ Temperature Over the Next Days", markers=True)
            st.plotly_chart(fig_temp, use_container_width=True)

            # 🌧️ Rain Probability Trend
            st.markdown("### 🌧️ Rain Probability Trend")
            fig_rain = px.bar(city_forecast_df, x="date", y="rain_probability",
                              title="🌧️ Rain Probability Over the Next Days",
                              labels={"rain_probability": "Rain Probability (%)"}, text="rain_probability")
            st.plotly_chart(fig_rain, use_container_width=True)

        else:
            st.warning("No forecast data available for this city.")