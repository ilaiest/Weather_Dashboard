import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# 🔹 Configuración de Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 NUEVO Service Account (Copiar los datos desde el JSON)
GOOGLE_CREDENTIALS = {
  "type": "service_account",
  "project_id": "weatherdashboard-451702",
  "private_key_id": "07957c723aedea4d2c24ed6647961f6e5ef87e97",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC0PxLYyOyorZer\n0UfvuhbC3jXTxRuCdIRkzidLCkWp+JyRO9aYp7V4Xn5nEcQmdwIufAhmOnxlH0LO\n1F0wRwq8V9qkrlOV95B+uP2oG89AR5PmlEdbUemxgSHUvWkkD3pf3UNJP667IVgF\nnBQj6+qZeb8KD0/u6izyA3DkpbgrtMqMwpR9PPpinXXZ5IY5UDWHakGuRpUT7HwA\nW8anj9PozOWVbl7e8qwa5AFabvRAjegvqBnIsNBnxXha7naKkXzfVa4pD6JREJW2\ntxC2tLZrBKzxJGA8z4Tmp4+Sd7B9iR/kJ5ok3r7JKrtyE45yxIV8ekYc99k6wxmT\n8kiXD4qbAgMBAAECggEAM8vgTZ3HrF1eNYjJhFFUkyEqFLYSxrVXCmTXk8/a3xJL\nY8zvSSUAmBuHdXT8ihUu8k7AVyg9cQ2/tBIAyYvQwPj6ItLZwEHJKzFb60A6mX04\nOk2oB80NO+4g27KmkS9FemDqIhWDz9CwK8SDYSM9YmdDB9AIp15yFgX5HiulNiGd\nTRpclxUwdzl6b/0sTxempDsLe1vG2XjbpoU6cFIArjspmZq8+8FnLuXftrhleAU8\n19OSYBB+T9a6ia9ExMlzK94LvTRg+X4ITEp7FDsgtagDk3Q5JfDnCrSNBqK36ZkT\nO1mR1BrlH+L/XIj0naoEGFrPcwTpb9JqNNYOiQDAKQKBgQDlcL7igL2Ofrik2IGY\nyYOlCZjO02d9KxNfd+Gbg0SelAoBYQvtBkq8ITDhi3Yy2BXNgXkXJNXNAPM1RAAo\nDIN3CbYEdrAeysxwt96SpFpI48V9Iu1BREXvvtIFhp29mgATgaOWb4/3upHiU7KF\nqYkT1cpq4LuNmU1bN9RFTEp1vQKBgQDJHIIknIT5PWfRfQj9t7wQ4WfqTmHzsanx\nB6SUadEZ17FYTpZqvnTsUJKkUfQzAB5SwFalLa2pULRoB7kHYsU0bXFXvX2exFUc\nk7GcamE2Lg1g1GcmqY97eEi0Q50uDjfRZfiWRix+FAvXx4A3CQCylKLyD37a3Y6s\nTgEDe0erNwKBgFCmoiLCeF9nggZIKL4JT+IqjnFddIpWIvgzDrX4nZ1UknPLpkKK\nLKkWzbTqrgDPXlKfyW3uP81RISy/G4L4axnj6vyEsAIS7WxN5coMRcRLdHc5WMbR\ndfgBTpgsqrQkNxSkRFm0G5pMFc3F+AHuB0ZWp1GMb8Ele0CuTkqRt7bNAoGBAJBJ\nJsnzjadvuctfhJLbPk9yGGbPI5F+NqmZzSc5n+6FhFQR1fLxf9uHlx3TOntYq2i9\nW6yYUA64uyYj3EkDQO7zUi0b40OEInglMnlBDUuc0LZWzUa8whdYXfkOxXckdkGC\ngk32PLeb1D9Uf5V8nQaCg0Fdgqqt6E2QjUOdL/cTAoGAHryXy2QRDHACVvOFt8qE\nMWM/ThxK9dj8UsflW6/P/+S5e5UE6Z7RmsyF3qH5T8lKpAXyBTu6eihioQ1nqPAr\n6RYOpTxWMr6i4n1i+dXieH5QDHV9AofYYEzyd+cCyXsbDcPk72idvNQaRVPtKrTZ\naqc0O/odu3Hu05Xl/C/2eYg=\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit@weatherdashboard-451702.iam.gserviceaccount.com",
  "client_id": "116816624603567048527",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit%40weatherdashboard-451702.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# 🔹 Crear credenciales y conectar con Google Sheets
try:
    creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Weather_Dashboard")
    st.success("✅ Conexión exitosa con Google Sheets usando el nuevo Service Account.")

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
    """Carga todos los datos desde Google Sheets una sola vez para optimización."""
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
            weather_icon = weather_icons.get(today_weather["weather_condition"].strip().lower(), "🌎")

            st.markdown(f"""
                <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; text-align: center;">
                    <h2 style="color: #00AEEF;">{selected_city} - {today_weather['date']}</h2>
                    <h1 style="font-size: 60px;">{weather_icon} {today_weather['temp']}°C</h1>
                    <p style="font-size: 20px;">Feels Like: {today_weather['feels_like']}°C</p>
                    <p style="font-size: 18px;">{today_weather['weather_condition']}</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("### 📈 Temperature Trends")
            fig_temp = px.line(city_forecast_df, x="date", y=["temp", "feels_like"],
                               labels={"value": "Temperature (°C)", "date": "Date"},
                               title="🌡️ Temperature Over the Next Days", markers=True)
            st.plotly_chart(fig_temp, use_container_width=True)

        else:
            st.warning("No forecast data available for this city.")
