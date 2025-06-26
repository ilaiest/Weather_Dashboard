import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Weather Operations Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- 2. WEATHER ICONS & SESSION STATE ---
weather_icons = {
    # Main Conditions
    "clouds": "☁️", "rain": "🌧️", "clear": "☀️", "thunderstorm": "⛈️",
    "snow": "❄️", "drizzle": "🌦️", "mist": "🌫️", "fog": "🌫️", "haze": "🌫️",
    "smoke": "🌫️", "dust": "💨", "sand": "💨", "ash": "🌋", "squall": "🌬️",
    "tornado": "🌪️",
    # Specific Conditions
    "clear sky": "☀️", "few clouds": "🌤️", "scattered clouds": "⛅", "broken clouds": "☁️",
    "overcast clouds": "🌥️", "shower rain": "🌦️", "light rain": "🌦️", "moderate rain": "🌧️",
}

if 'page' not in st.session_state:
    st.session_state.page = 'General Dashboard'
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None

# --- 3. DATA LOADING ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        spreadsheet = client.open("Weather_Dashboard")
        data_dict = {}
        sheets_to_load = {"daily": "Data", "hourly": "Hourly Forecast", "alerts": "Weather Alerts", "clusters": "City_Team_Cluster"}
        for key, name in sheets_to_load.items():
            ws = spreadsheet.worksheet(name)
            df = pd.DataFrame(ws.get_all_records())
            data_dict[key] = df
        
        # --- Data Type and Timezone Processing ---
        
        # Daily Data
        daily_df = data_dict['daily']
        daily_df["date"] = pd.to_datetime(daily_df["date"]).dt.date
        numeric_cols_daily = ["temp", "feels_like", "humidity", "rain_probability", "wind_speed", "total_rain_mm", "temp_max", "temp_min", "uvi"]
        for col in numeric_cols_daily: daily_df[col] = pd.to_numeric(daily_df[col], errors='coerce')
        data_dict['daily'] = daily_df
        
        # ⭐ CAMBIO: Conversión de zona horaria para datos por hora
        hourly_df = data_dict['hourly']
        hourly_df["forecast_time"] = pd.to_datetime(hourly_df["forecast_time"]).dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City')
        numeric_cols_hourly = ["temp", "feels_like", "humidity", "rain_probability", "rain_1h", "wind_speed"]
        for col in numeric_cols_hourly: hourly_df[col] = pd.to_numeric(hourly_df[col], errors='coerce')
        data_dict['hourly'] = hourly_df
        
        # ⭐ CAMBIO: Conversión de zona horaria para alertas
        alerts_df = data_dict['alerts']
        if not alerts_df.empty and 'start_time' in alerts_df.columns:
            alerts_df["start_time"] = pd.to_datetime(alerts_df["start_time"]).dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City')
            alerts_df["end_time"] = pd.to_datetime(alerts_df["end_time"]).dt.tz_localize('UTC').dt.tz_convert('America/Mexico_City')
        data_dict['alerts'] = alerts_df
        
        return data_dict
    except Exception as e:
        st.error(f"❌ Error loading data from Google Sheets: {e}")
        return None

# --- 4. MAIN LOGIC ---
all_data = load_all_data()

def set_page(page_name, city_name=None):
    st.session_state.page = page_name
    st.session_state.selected_city = city_name

# --- HEADER BAR ---
header = st.container()
# ... (código del header sin cambios) ...
with header:
    cols = st.columns([2, 4, 2])
    with cols[0]:
        if st.button("🏠 General Dashboard", use_container_width=True):
            set_page('General Dashboard', None)
            st.rerun()
    if all_data:
        with cols[1]:
            daily_df_merged = pd.merge(all_data['daily'], all_data['clusters'], on="city", how="left")
            all_cities = [""] + sorted(daily_df_merged['city'].unique().tolist())
            current_city_index = all_cities.index(st.session_state.selected_city) if st.session_state.selected_city in all_cities else 0
            search_city = st.selectbox("Search for a city...", all_cities, index=current_city_index, label_visibility="collapsed", placeholder="Type to search for a city...")
            if search_city and search_city != st.session_state.selected_city:
                set_page('Detailed Analysis', search_city)
                st.rerun()

st.markdown("---")

# --- VIEW 1: GENERAL DASHBOARD ---
if st.session_state.page == 'General Dashboard' and all_data:
    # ... (código del dashboard general sin cambios) ...
    st.title("🌍 General Weather Dashboard")
    with st.expander("🔍 Show Advanced Filters"):
        filter_cols = st.columns(4)
        with filter_cols[0]: selected_date_main = st.date_input("📅 Date", datetime.today().date())
        with filter_cols[1]:
            countries = ["All"] + sorted(daily_df_merged['country_code'].unique().tolist())
            selected_country = st.selectbox("🌎 Country", countries)
        with filter_cols[2]:
            teams = ["All"] + sorted(daily_df_merged['team'].dropna().unique().tolist())
            selected_team = st.selectbox("🏢 Team", teams)
        with filter_cols[3]:
            clusters = ["All"] + sorted(daily_df_merged['cluster'].dropna().unique().tolist())
            selected_cluster = st.selectbox("📍 Cluster", clusters)

    filtered_df = daily_df_merged[daily_df_merged["date"] == selected_date_main]
    if selected_country != "All": filtered_df = filtered_df[filtered_df["country_code"] == selected_country]
    if selected_team != "All": filtered_df = filtered_df[filtered_df["team"] == selected_team]
    if selected_cluster != "All": filtered_df = filtered_df[filtered_df["cluster"] == selected_cluster]
    st.subheader(f"🏙️ City Overview for {selected_date_main.strftime('%b %d, %Y')}")
    if not filtered_df.empty:
        weather_df_sorted = filtered_df.sort_values(by="rain_probability", ascending=False)
        alerts_df = all_data['alerts']
        num_columns = 4
        columns = st.columns(num_columns)
        for i, row in enumerate(weather_df_sorted.itertuples()):
            col = columns[i % num_columns]
            with col:
                with st.container(border=True, height=300):
                    main_cond = str(row.main_condition).lower().strip()
                    weather_cond = str(row.weather_condition).lower().strip()
                    weather_icon = weather_icons.get(weather_cond, weather_icons.get(main_cond, "🌎"))
                    active_alert = alerts_df[(alerts_df['city'] == row.city) & (alerts_df['start_time'].dt.date <= selected_date_main) & (alerts_df['end_time'].dt.date >= selected_date_main)]
                    alert_icon = " 🚨" if not active_alert.empty else ""
                    st.markdown(f"<h6>{weather_icon} {row.city}{alert_icon}</h6>", unsafe_allow_html=True)
                    st.markdown(f"""<p style="font-size: 14px; margin-bottom: 5px;">
                                🌡️ Temp: <b>{row.temp_min}°C / {row.temp_max}°C</b><br>
                                ☀️ UV Index: <b>{row.uvi}</b><br>
                                💧 Humidity: {row.humidity}%<br>
                                🌧️ Rain: <b>{row.rain_probability}%</b> ({row.total_rain_mm} mm)
                                </p>""", unsafe_allow_html=True)
                    if not active_alert.empty:
                        with st.expander("View Alert"):
                            st.warning(f"**{active_alert.iloc[0]['event']}**\n\n_{active_alert.iloc[0]['description']}_")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Details 📈", key=f"btn_{row.Index}", use_container_width=True):
                        set_page('Detailed Analysis', row.city)
                        st.rerun()
    else:
        st.warning("No weather data available for the selected filters.")


# --- VIEW 2: DETAILED ANALYSIS ---
elif st.session_state.page == 'Detailed Analysis' and all_data:
    selected_city = st.session_state.selected_city
    if selected_city:
        title_cols = st.columns([3, 1])
        with title_cols[0]: st.title(f"📊 Detailed Analysis for: {selected_city}")
        with title_cols[1]: selected_date_detail = st.date_input("Select Date", datetime.today().date(), label_visibility="collapsed")

        alerts_df = all_data['alerts']
        city_active_alerts = alerts_df[(alerts_df['city'] == selected_city) & (alerts_df['start_time'].dt.date <= selected_date_detail) & (alerts_df['end_time'].dt.date >= selected_date_detail)]
        if not city_active_alerts.empty:
            st.subheader("🚨 Active Alert(s) for this Day")
            for _, alert in city_active_alerts.iterrows():
                st.warning(f"**{alert['event']}** (Source: {alert['sender_name']})\n\n"
                           f"**Description:** {alert['description']}\n\n"
                           f"**Active from:** {alert['start_time'].strftime('%Y-%m-%d')} **to** {alert['end_time'].strftime('%Y-%m-%d')}")
            st.markdown("---")
        
        city_daily_df = all_data['daily'][all_data['daily']['city'] == selected_city]
        
        st.subheader(f"🗓️ 7-Day Summary from {selected_date_detail.strftime('%b %d')}")
        future_forecast_preview = city_daily_df[city_daily_df['date'] >= selected_date_detail].head(7)
        if not future_forecast_preview.empty:
            forecast_cols = st.columns(len(future_forecast_preview))
            for idx, (_, row) in enumerate(future_forecast_preview.iterrows()):
                with forecast_cols[idx]:
                    with st.container(border=True):
                        main_cond = str(row['main_condition']).lower().strip()
                        weather_cond = str(row['weather_condition']).lower().strip()
                        forecast_icon = weather_icons.get(weather_cond, weather_icons.get(main_cond, "🌎"))
                        st.markdown(f"""<div style="text-align: center; height: 150px;">
                                        <h6>{row['date'].strftime('%a, %d')}</h6>
                                        <p style="font-size: 35px; margin-top: -10px; margin-bottom: 0px;">{forecast_icon}</p>
                                        <p style="margin-bottom: 2px;"><b>{row['temp_max']}°</b> / {row['temp_min']}°</p>
                                        <p style="font-size: 12px;">{str(row['weather_condition']).capitalize()}</p>
                                    </div>""", unsafe_allow_html=True)
        st.markdown("---") 

        if selected_date_detail == datetime.today().date():
            st.subheader(f"🕒 Forecast for the Next 48 Hours")
            city_hourly_df = all_data['hourly'][all_data['hourly']['city'] == selected_city]
            
            # ⭐ CAMBIO: Usamos la hora actual de CDMX para el filtro
            now_cdmx = pd.Timestamp.now(tz='America/Mexico_City')
            hourly_forecast_range = city_hourly_df[(city_hourly_df['forecast_time'] >= now_cdmx) & (city_hourly_df['forecast_time'] <= now_cdmx + timedelta(hours=48))]
            
            if not hourly_forecast_range.empty:
                rain_text_labels = hourly_forecast_range['rain_1h'].apply(lambda x: f'{x:.1f} mm' if x > 0 else '')
                fig_hourly = go.Figure()
                fig_hourly.add_trace(go.Scatter(x=hourly_forecast_range['forecast_time'], y=hourly_forecast_range['temp'], mode='lines+markers', name='Temperature (°C)', yaxis='y1', line=dict(color='orange')))
                fig_hourly.add_trace(go.Bar(x=hourly_forecast_range['forecast_time'], y=hourly_forecast_range['rain_probability'], name='Rain Probability (%)', yaxis='y2', marker_color='blue', opacity=0.6, text=rain_text_labels, textposition='outside'))
                fig_hourly.update_layout(title_text="Hourly Temperature & Rain Probability", yaxis=dict(title="Temperature (°C)", color='orange'), yaxis2=dict(title="Rain Probability (%)", overlaying='y', side='right', range=[0, 100], color='blue'), legend=dict(x=0, y=1.2, orientation="h"))
                # ⭐ Indicamos a la gráfica que el eje X está en la zona horaria de CDMX
                fig_hourly.update_xaxes(title_text="Time (America/Mexico_City)")
                st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("Hourly forecast is only available for the current day.")

         st.subheader(f"📈 8-Day Trend: Temperature & UV Index")
        future_forecast_trend = city_daily_df[city_daily_df['date'] >= selected_date_detail].head(8)
        if not future_forecast_trend.empty:
            # Crear una figura con un eje Y secundario
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Añadir las líneas de Temperatura (usarán el eje Y primario)
            fig.add_trace(go.Scatter(x=future_forecast_trend['date'], y=future_forecast_trend['temp_max'],
                                     mode='lines+markers', name='Max Temp', line=dict(color='red')),
                          secondary_y=False)
            fig.add_trace(go.Scatter(x=future_forecast_trend['date'], y=future_forecast_trend['temp_min'],
                                     mode='lines+markers', name='Min Temp', line=dict(color='lightblue'),
                                     fill='tonexty', fillcolor='rgba(255, 165, 0, 0.2)'),
                          secondary_y=False)

            # Añadir las barras de Índice UV (usarán el eje Y secundario)
            fig.add_trace(go.Bar(x=future_forecast_trend['date'], y=future_forecast_trend['uvi'],
                                 name='UV Index', marker_color='purple', opacity=0.5,
                                 text=future_forecast_trend['uvi'].round(1)),
                          secondary_y=True)

            # Configurar los títulos y los ejes
            fig.update_layout(
                title_text="Temperature Range & UV Index",
                legend=dict(x=0, y=1.2, orientation="h")
            )
            fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
            fig.update_yaxes(title_text="UV Index", secondary_y=True, range=[0, future_forecast_trend['uvi'].max() + 2])

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Use the search bar in the header to find a city.")
elif not all_data:
    st.error("Could not load data. Please check the connection to Google Sheets and the configuration.")
