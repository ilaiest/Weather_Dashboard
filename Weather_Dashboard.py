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
    "clear sky": "☀️", "few clouds": "🌤️", "scattered clouds": "⛅", "broken clouds": "☁️",
    "overcast clouds": "🌥️", "drizzle": "🌦️", "light rain": "🌦️", "moderate rain": "🌧️",
    "heavy rain": "🌧️", "thunderstorm": "⛈️", "snow": "❄️", "mist": "🌫️", "fog": "🌫️",
    "haze": "🌁", "smoke": "🌫️", "dust": "💨", "sand": "💨", "volcanic ash": "🌋",
    "squalls": "🌬️", "tornado": "🌪️"
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
    """Carga datos de Google Sheets asegurando que `rain_probability` y `rain_hours` sean strings."""
    try:
        worksheet = spreadsheet.worksheet("Data")
        data = worksheet.get_all_values()
        if not data:
            return pd.DataFrame(), pd.DataFrame()

        weather_df = pd.DataFrame(data[1:], columns=data[0])
        weather_df["date"] = pd.to_datetime(weather_df["date"], format="%Y-%m-%d", errors="coerce").dt.date

        # ✅ Convertir solo columnas numéricas a `float`
        numeric_cols = ["temp", "feels_like", "wind_speed", "humidity"]
        for col in numeric_cols:
            weather_df[col] = pd.to_numeric(weather_df[col], errors="coerce")

        # ✅ Mantener `rain_probability` y `rain_hours` como `string`
        weather_df["rain_probability"] = weather_df["rain_probability"].astype(str).replace("", "No Data")
        weather_df["rain_hours"] = weather_df["rain_hours"].astype(str).replace("None", "No Rain").replace("", "No Rain")

        # Cargar equipo y clusters
        team_worksheet = spreadsheet.worksheet("City_Team_Cluster")
        team_data = team_worksheet.get_all_values()
        team_df = pd.DataFrame(team_data[1:], columns=team_data[0]) if team_data else pd.DataFrame()

        return weather_df, team_df
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame(), pd.DataFrame()



# 🔹 **Función para obtener datos de clima filtrados**
def fetch_weather_data(selected_date, selected_country, selected_team, selected_cluster):
    weather_df, team_df = load_google_sheets()

    if weather_df.empty:
        return pd.DataFrame()

    weather_df = weather_df[weather_df["date"] == selected_date]

    if not team_df.empty and "city" in weather_df.columns and "city" in team_df.columns:
        weather_df = weather_df.merge(team_df, on="city", how="left")

    # Filtrar por país si se seleccionó un país específico
    if "country_code" in weather_df.columns and selected_country != "All":
        weather_df = weather_df[weather_df["country_code"] == selected_country]

    # Filtrar por equipo (team)
    if "team" in weather_df.columns and selected_team != "All":
        weather_df = weather_df[weather_df["team"] == selected_team]

    # Filtrar por cluster
    if "cluster" in weather_df.columns and selected_cluster != "All":
        if selected_cluster in weather_df["cluster"].unique():
            weather_df = weather_df[weather_df["cluster"] == selected_cluster]
        else:
            st.warning(f"No hay datos para el cluster '{selected_cluster}'. Mostrando todos los datos.")

    return weather_df


# 🔹 **Función para obtener el pronóstico de una ciudad en los próximos días**
def fetch_city_forecast(selected_city, selected_date, selected_country):
    weather_df, team_df = load_google_sheets()

    if weather_df.empty:
        return pd.DataFrame()

    forecast_df = weather_df[weather_df["city"] == selected_city].copy()

    # Filtrar por país si se seleccionó un país específico
    if "country_code" in forecast_df.columns and selected_country != "All":
        forecast_df = forecast_df[forecast_df["country_code"] == selected_country]

    forecast_df["date"] = pd.to_datetime(forecast_df["date"], format="%Y-%m-%d", errors="coerce").dt.date
    forecast_df = forecast_df[forecast_df["date"] >= selected_date].sort_values("date").head(5)

    return forecast_df




# 🚀 **Sidebar: Selección de Vista**
st.sidebar.markdown("## 🌎 **Weather Navigation**", unsafe_allow_html=True)
page = st.sidebar.radio("", ["🌍 City Overview", "📊 Detailed Forecast"], label_visibility="collapsed")

# 📅 **Filtros**
selected_date = st.sidebar.date_input("📅 Select Date", datetime.today().date())
selected_country = st.sidebar.selectbox("🌎 Select Country", ["All", "MX", "CL", "AR", "CO", "CR", "DO", "EC"])
selected_team = st.sidebar.selectbox("🏢 Select Team", ["All", "MX", "POC", "CASA"])
selected_cluster = st.sidebar.selectbox("📍 Select Cluster",
                                        ["All", "Growers", "Heros", "POC Academy", "POC LAB", "Rocket"])

# 🌍 **City Overview**
if page == "🌍 City Overview":
    st.markdown(f"## 🌍 Weather Overview for {selected_date}")

    # Aplicar los filtros existentes
    weather_df = fetch_weather_data(selected_date, selected_country, selected_team, selected_cluster)

    if not weather_df.empty:
        # Convertir `rain_probability` a numérico para ordenar correctamente
        weather_df["rain_probability_numeric"] = pd.to_numeric(
            weather_df["rain_probability"].str.replace("%", "", regex=True), errors="coerce"
        ).fillna(0)

        # Ordenar de mayor a menor según `rain_probability_numeric`
        weather_df = weather_df.sort_values(by="rain_probability_numeric", ascending=False)

        # Volver a formatear `rain_probability` con `%` para la visualización
        weather_df["rain_probability"] = weather_df["rain_probability_numeric"].astype(int).astype(str) + "%"

        # Definir el número de columnas dinámicamente para evitar saltos
        num_columns = min(3, len(weather_df))
        columns = st.columns(num_columns)

        # Distribuir tarjetas sin saltos
        for i, row in enumerate(weather_df.itertuples()):
            col = columns[i % num_columns]  # Asegura que las tarjetas llenen bien las columnas
            with col:
                weather_icon = weather_icons.get(row.weather_condition, "🌎")
                st.markdown(
                    f"""
                    <div style="border-radius: 10px; padding: 15px; background-color: #1E1E1E; color: white; margin-bottom: 10px;">
                        <h3>{weather_icon} {row.city}</h3>
                        <p>🌡️ Temperature: {row.temp}°C | Feels Like: {row.feels_like}°C</p>
                        <p>🌬️ Wind Speed: {row.wind_speed} km/h</p>
                        <p>💧 Humidity: {row.humidity}%</p>
                        <p>🌧️ Rain Probability: {row.rain_probability}</p>
                        <p>⏳ Rain Hours: {row.rain_hours if row.rain_hours else 'No Rain Expected'}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
    else:
        st.warning("No weather data available for the selected filters.")

# 📊 **Detailed Forecast**
elif page == "📊 Detailed Forecast":
    st.markdown("## 📊 5-Day Forecast")

    available_cities_df = fetch_weather_data(selected_date, selected_country, selected_team, selected_cluster)
    available_cities = available_cities_df["city"].unique().tolist() if not available_cities_df.empty else []

    city_list = ["Select a City"] + available_cities
    selected_city = st.selectbox("🏙️ Choose a City", city_list)

    if selected_city != "Select a City":
        city_forecast_df = fetch_city_forecast(selected_city, selected_date, selected_country)

        if not city_forecast_df.empty:
            today_weather = city_forecast_df.iloc[0]
            normalized_condition = today_weather["weather_condition"].strip().lower()
            weather_icon = weather_icons.get(normalized_condition, "🌎")

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
        st.markdown("<h3 style='color:#00AEEF; text-align: center;'>🌤️ Next Days Weather Forecast</h3>",
                    unsafe_allow_html=True)

        forecast_cols = st.columns(len(city_forecast_df))  # Crear columnas dinámicas

        # 🔹 Corrección del Error IndexError
        if not city_forecast_df.empty:  # ✅ Evita error si `city_forecast_df` está vacío
            num_days = len(city_forecast_df)  # ✅ Número de días disponibles en el pronóstico
            forecast_cols = st.columns(num_days)  # ✅ Crear columnas dinámicas según la cantidad de días

            for idx, row in enumerate(
                    city_forecast_df.itertuples()):  # ✅ `enumerate()` asegura que `idx` siempre esté en rango
                forecast_icon = weather_icons.get(row.weather_condition.strip().lower(), "🌎")
                with forecast_cols[idx]:  # ✅ Ahora `idx` no podrá exceder el número de columnas
                    st.markdown(f"""
                    <div style="border-radius: 10px; padding: 20px; background-color: #2E2E2E; color: white; text-align: center;
                                width: 150px; height: 160px; margin-left: auto;">
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
