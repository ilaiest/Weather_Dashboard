import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Weather Operations Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- 2. DICCIONARIO DE ICONOS Y ESTADO DE SESIÓN ---
weather_icons = {
    "clear sky": "☀️", "few clouds": "🌤️", "scattered clouds": "⛅", "broken clouds": "☁️",
    "overcast clouds": "🌥️", "drizzle": "🌦️", "light rain": "🌦️", "moderate rain": "🌧️",
    "heavy rain": "🌧️", "thunderstorm": "⛈️", "snow": "❄️", "mist": "🌫️", "fog": "🌫️",
    "haze": "🌁", "smoke": "🌫️", "dust": "💨", "sand": "💨", "volcanic ash": "🌋",
    "squalls": "🌬️", "tornado": "🌪️"
}

if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard General'
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None

# --- 3. AUTENTICACIÓN Y CARGA DE DATOS ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        spreadsheet = client.open("Weather_Dashboard")
        data_dict = {}
        # Cargar todas las hojas...
        sheets_to_load = {
            "daily": "Data", "hourly": "Hourly Forecast",
            "alerts": "Weather Alerts", "clusters": "City_Team_Cluster"
        }
        for key, name in sheets_to_load.items():
            ws = spreadsheet.worksheet(name)
            df = pd.DataFrame(ws.get_all_records())
            data_dict[key] = df
        
        # Procesamiento de Tipos de Datos
        # Daily
        daily_df = data_dict['daily']
        daily_df["date"] = pd.to_datetime(daily_df["date"]).dt.date
        numeric_cols_daily = ["temp", "feels_like", "humidity", "rain_probability", "wind_speed", "total_rain_mm", "temp_max", "temp_min", "uvi"]
        for col in numeric_cols_daily: daily_df[col] = pd.to_numeric(daily_df[col], errors='coerce')
        data_dict['daily'] = daily_df
        # Hourly
        hourly_df = data_dict['hourly']
        hourly_df["forecast_time"] = pd.to_datetime(hourly_df["forecast_time"])
        numeric_cols_hourly = ["temp", "feels_like", "humidity", "rain_probability", "rain_1h", "wind_speed"]
        for col in numeric_cols_hourly: hourly_df[col] = pd.to_numeric(hourly_df[col], errors='coerce')
        data_dict['hourly'] = hourly_df
        # Alerts
        alerts_df = data_dict['alerts']
        if not alerts_df.empty:
            alerts_df["start_time"] = pd.to_datetime(alerts_df["start_time"])
            alerts_df["end_time"] = pd.to_datetime(alerts_df["end_time"])
        data_dict['alerts'] = alerts_df
        
        return data_dict
    except Exception as e:
        st.error(f"❌ Error cargando los datos desde Google Sheets: {e}")
        return None

# --- 4. LÓGICA PRINCIPAL ---
all_data = load_all_data()

def set_page(page_name, city_name=None):
    st.session_state.page = page_name
    st.session_state.selected_city = city_name

# --- BARRA DE ENCABEZADO PRINCIPAL ---
header = st.container()
with header:
    cols = st.columns([2, 4, 2])
    with cols[0]:
        if st.button("🏠 Dashboard General", use_container_width=True):
            set_page('Dashboard General', None)
            st.rerun()
    
    if all_data:
        with cols[1]:
            daily_df_merged = pd.merge(all_data['daily'], all_data['clusters'], on="city", how="left")
            all_cities = [""] + sorted(daily_df_merged['city'].unique().tolist())
            
            # Si estamos en una vista detallada, mostramos la ciudad actual en el buscador
            current_city_index = all_cities.index(st.session_state.selected_city) if st.session_state.selected_city in all_cities else 0

            search_city = st.selectbox(
                "Busca una ciudad para ver su detalle...", all_cities, 
                index=current_city_index, label_visibility="collapsed", placeholder="Escribe para buscar..."
            )
            
            # Si el usuario selecciona una nueva ciudad en el buscador
            if search_city and search_city != st.session_state.selected_city:
                set_page('Análisis por Ciudad', search_city)
                st.rerun()

st.markdown("---")


# --- VISTA 1: DASHBOARD GENERAL ---
if st.session_state.page == 'Dashboard General' and all_data:
    st.title("🌍 Dashboard General del Clima")
    
    # Filtros ahora dentro de un expander
    with st.expander("🔍 Mostrar Filtros Avanzados"):
        filter_cols = st.columns(4)
        with filter_cols[0]:
            selected_date = st.date_input("📅 Fecha", datetime.today().date())
        with filter_cols[1]:
            countries = ["Todos"] + sorted(daily_df_merged['country_code'].unique().tolist())
            selected_country = st.selectbox("🌎 País", countries)
        with filter_cols[2]:
            teams = ["Todos"] + sorted(daily_df_merged['team'].dropna().unique().tolist())
            selected_team = st.selectbox("🏢 Equipo", teams)
        with filter_cols[3]:
            clusters = ["Todos"] + sorted(daily_df_merged['cluster'].dropna().unique().tolist())
            selected_cluster = st.selectbox("📍 Cluster", clusters)

    # Aplicar filtros
    filtered_df = daily_df_merged[daily_df_merged["date"] == selected_date]
    if selected_country != "Todos": filtered_df = filtered_df[filtered_df["country_code"] == selected_country]
    if selected_team != "Todos": filtered_df = filtered_df[filtered_df["team"] == selected_team]
    if selected_cluster != "Todos": filtered_df = filtered_df[filtered_df["cluster"] == selected_cluster]
    
    # Panel de Alertas
    st.subheader("🚨 Alertas Gubernamentales Activas")
    # ... (código de alertas sin cambios)
    alerts_df = all_data['alerts']
    cities_in_view = filtered_df['city'].unique()
    active_alerts = alerts_df[(alerts_df['city'].isin(cities_in_view)) & (alerts_df['start_time'].dt.date <= selected_date) & (alerts_df['end_time'].dt.date >= selected_date)]
    if not active_alerts.empty:
        with st.expander(f"⚠️ Se encontraron {len(active_alerts)} alertas activas. Haz clic para ver detalles.", expanded=True):
            for _, alert in active_alerts.iterrows(): st.warning(f"**{alert['city']}: {alert['event']}** (Fuente: {alert['sender_name']})\n_{alert['description']}_")
    else:
        st.success("✅ No hay alertas gubernamentales activas para las ciudades seleccionadas.")
    st.markdown("---")
    
    st.subheader(f"🏙️ Resumen por Ciudad para el {selected_date.strftime('%d %b, %Y')}")
    if not filtered_df.empty:
        weather_df_sorted = filtered_df.sort_values(by="rain_probability", ascending=False)
        num_columns = 4 # Podemos usar 4 columnas ahora que no hay sidebar
        columns = st.columns(num_columns)
        
        for i, row in enumerate(weather_df_sorted.itertuples()):
            col = columns[i % num_columns]
            with col:
                with st.container(border=True):
                    weather_icon = weather_icons.get(row.weather_condition.lower(), "🌎")
                    st.markdown(f"<h5>{weather_icon} {row.city}</h5>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <p style="font-size: 13px;">
                        🌡️ Temp: <b>{row.temp_min}°C / {row.temp_max}°C</b><br>
                        ☀️ UV: <b>{row.uvi}</b> | 💧 Humedad: {row.humidity}%<br>
                        🌧️ Lluvia: <b>{row.rain_probability}%</b> ({row.total_rain_mm} mm)
                        </p>
                    """, unsafe_allow_html=True)
                    if st.button("Ver Análisis 📈", key=f"btn_{row.Index}", use_container_width=True, type="primary"):
                        set_page('Análisis por Ciudad', row.city)
                        st.rerun()
    else:
        st.warning("No hay datos de clima para los filtros seleccionados.")

# --- VISTA 2: ANÁLISIS POR CIUDAD ---
elif st.session_state.page == 'Análisis por Ciudad' and all_data:
    selected_city = st.session_state.selected_city
    
    if selected_city:
        st.title(f"📊 Análisis Detallado para: {selected_city}")
        
        # Lógica de la página de detalle (sin cambios, solo se alimenta de `selected_city`)
        city_daily_df = all_data['daily'][all_data['daily']['city'] == selected_city]
        city_hourly_df = all_data['hourly'][all_data['hourly']['city'] == selected_city]
        current_date = datetime.today().date() # Usamos la fecha actual para el pronóstico
        
        # Gráfico de Pronóstico por Hora
        st.subheader(f"🕒 Pronóstico para las Próximas 48 Horas")
        now = pd.Timestamp.now(tz='UTC').tz_localize(None) # Usamos UTC naive para comparar
        hourly_forecast_range = city_hourly_df[(city_hourly_df['forecast_time'] >= now) & (city_hourly_df['forecast_time'] <= now + timedelta(hours=48))]
        if not hourly_forecast_range.empty:
            fig_hourly = go.Figure()
            fig_hourly.add_trace(go.Scatter(x=hourly_forecast_range['forecast_time'], y=hourly_forecast_range['temp'], mode='lines+markers', name='Temperatura (°C)', yaxis='y1', line=dict(color='orange')))
            fig_hourly.add_trace(go.Bar(x=hourly_forecast_range['forecast_time'], y=hourly_forecast_range['rain_probability'], name='Prob. Lluvia (%)', yaxis='y2', marker_color='blue', opacity=0.6))
            fig_hourly.update_layout(title_text="Temperatura y Probabilidad de Lluvia por Hora", yaxis=dict(title="Temperatura (°C)", color='orange'), yaxis2=dict(title="Probabilidad de Lluvia (%)", overlaying='y', side='right', range=[0, 100], color='blue'), legend=dict(x=0, y=1.1, orientation="h"))
            st.plotly_chart(fig_hourly, use_container_width=True)

        # Pronóstico Diario
        st.subheader(f"🗓️ Pronóstico para los Próximos 8 Días")
        future_forecast = city_daily_df[city_daily_df['date'] >= current_date].head(8)
        if not future_forecast.empty:
            fig_temp_range = go.Figure()
            fig_temp_range.add_trace(go.Scatter(x=future_forecast['date'], y=future_forecast['temp_max'], mode='lines+markers', name='Temp. Máxima', line=dict(color='red'), text=future_forecast['temp_max'].apply(lambda x: f'{x}°')))
            fig_temp_range.add_trace(go.Scatter(x=future_forecast['date'], y=future_forecast['temp_min'], mode='lines+markers', name='Temp. Mínima', line=dict(color='lightblue'), fill='tonexty', fillcolor='rgba(255, 165, 0, 0.2)', text=future_forecast['temp_min'].apply(lambda x: f'{x}°')))
            fig_temp_range.update_layout(title="Rango de Temperatura para los Próximos Días", yaxis_title="Temperatura (°C)")
            st.plotly_chart(fig_temp_range, use_container_width=True)
        else:
            st.warning("No hay datos de pronóstico futuro para esta ciudad.")
            
    else:
        st.info("Usa la barra de búsqueda en el encabezado para encontrar una ciudad.")

elif not all_data:
    st.error("No se pudieron cargar los datos. Por favor, revisa la conexión y la configuración de Google Sheets.")
