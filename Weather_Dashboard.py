import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# 🚀 **Debe ser la primera línea de Streamlit**
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# 🔹 **Configuración de Google Sheets**
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Weather_Dashboard")
    st.success("✅ Conexión exitosa con Google Sheets.")
except Exception as e:
    st.error(f"❌ Error al autenticar con Google Sheets: {e}")
    st.stop()

# 🔹 **Diccionario de Iconos de Clima**
weather_icons = {
    "clear sky": "☀️", "few clouds": "🌤️", "scattered clouds": "⛅", "broken clouds": "☁️",
    "overcast clouds": "🌥️", "drizzle": "🌦️", "light rain": "🌦️", "moderate rain": "🌧️",
    "heavy rain": "🌧️", "thunderstorm": "⛈️", "snow": "❄️", "mist": "🌫️", "fog": "🌫️",
    "haze": "🌁", "smoke": "🌫️", "dust": "💨", "sand": "💨", "volcanic ash": "🌋",
    "squalls": "🌬️", "tornado": "🌪️"
}

@st.cache_data
def load_google_sheets():
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        weather_df = pd.DataFrame(data[1:], columns=data[0])
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date
        numeric_cols = ["temp", "feels_like", "wind_speed", "humidity", "rain_probability", "rain_hours"]
        for col in numeric_cols:
            weather_df[col] = pd.to_numeric(weather_df[col], errors="coerce")
        return weather_df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame()

def fetch_weather_data(selected_date, selected_team, selected_cluster):
    weather_df = load_google_sheets()
    return weather_df[weather_df["date"] == selected_date]

def fetch_city_forecast(selected_city):
    weather_df = load_google_sheets()
    return weather_df[weather_df["city"] == selected_city]

# 🚀 Sidebar: View Selection
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 Filters
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today())
selected_date = selected_date.strftime("%Y-%m-%d")
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster",
                                        ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 SECTION 1: City Overview
if page == "🌍 City Overview":
    st.markdown(f"## 🌍 Weather Overview for {selected_date}")
    weather_df = fetch_weather_data(selected_date, selected_team, selected_cluster)

    if not weather_df.empty:
        cols = st.columns(3)
        for idx, row in weather_df.iterrows():
            weather_icon = weather_icons.get(row['main_condition'], "🌎")
            with cols[idx % 3]:
                st.markdown(f"""
                    <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; margin-bottom: 10px;">
                        <h3>{weather_icon} {row['city']}</h3>
                        <p>🌡️ Temperature: {row['temp']}°C | Feels Like: {row['feels_like']}°C</p>
                        <p>🌬️ Wind Speed: {row['wind_speed']} km/h</p>
                        <p>💧 Humidity: {row['humidity']}%</p>
                        <p>🌧️ Rain Probability: {row['rain_probability']}</p>
                        <p>⏳ Rain Hours: {row['rain_hours'] if row['rain_hours'] else 'No Rain Expected'}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No weather data available for the selected filters.")

# 📊 SECTION 2: Detailed Forecast
elif page == "📊 Detailed Forecast":
    st.markdown("## 📊 5-Day Forecast")
    city_list = ["Select a City"] + fetch_weather_data(selected_date, selected_team, selected_cluster)["city"].unique().tolist()
    selected_city = st.selectbox("🏙️ Choose a City", city_list)
    
    if selected_city != "Select a City":
        city_forecast_df = fetch_city_forecast(selected_city)

        if not city_forecast_df.empty:
            today_weather = city_forecast_df.iloc[0]
            weather_icon = weather_icons.get(today_weather["weather_condition"].strip().lower(), "🌎")
            
            st.markdown(f"""
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; text-align: center;">
                    <h2 style="color: #00AEEF;">{selected_city} - {today_weather['date']}</h2>
                    <h1 style="font-size: 60px;">{weather_icon} {today_weather['temp']}°C</h1>
                    <p>🌬️ Wind Speed: {today_weather['wind_speed']} km/h | 💧 Humidity: {today_weather['humidity']}%</p>
                    <p>🌧️ Rain Probability: {today_weather['rain_probability']}%</p>
                </div>
            """, unsafe_allow_html=True)
