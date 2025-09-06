import time
import requests
import psycopg2
from datetime import datetime
import concurrent.futures
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from cities import cities

# --- 1. CONFIGURACIÓN GENERAL ---
API_KEY = 'your api key'
BASE_URL = 'https://api.openweathermap.org/data/3.0/onecall'
PG_CONFIG = {"host": "localhost", "database": "weather_db", "user": "postgres", "password": "password"}
SHEET_NAME = "Weather_Dashboard"
DAILY_SHEET_NAME = "Data"
HOURLY_SHEET_NAME = "Hourly Forecast"
ALERTS_SHEET_NAME = "Weather Alerts"
CLUSTER_SHEET_NAME = "City_Team_Cluster"


# --- 2. FUNCIONES DEL PIPELINE ---

def connect_db():
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return None



def fetch_weather_data(city, lat, lon):
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': 'metric', 'exclude': 'minutely', 'lang': 'en'}
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        return city, response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la API para {city}: {e}")
        return city, None


def fetch_and_store_weather_data():
    print("--- INICIANDO PASO 1: Actualizar Base de Datos desde API ---")
    start_time = time.time()
    all_hourly_data, all_alerts_data, all_daily_data = [], [], []
    city_items = list(cities.items())
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_city = {executor.submit(fetch_weather_data, city, coords[0], coords[1]): city for city, coords in
                          city_items}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_city)):
            city, data = future.result()
            print(f"({i + 1}/{len(city_items)}) Obteniendo datos para: {city}")
            if data:
                if 'hourly' in data:
                    for hour_data in data['hourly']: all_hourly_data.append(
                        {'city': city, 'forecast_time': datetime.fromtimestamp(hour_data['dt']),
                         'temp': round(hour_data.get('temp', 0), 2),
                         'feels_like': round(hour_data.get('feels_like', 0), 2),
                         'humidity': round(hour_data.get('humidity', 0), 2),
                         'weather_condition': hour_data['weather'][0].get('description', ''),
                         'main_condition': hour_data['weather'][0].get('main', ''),
                         'rain_probability': round(hour_data.get('pop', 0) * 100, 2),
                         'rain_1h': hour_data.get('rain', {}).get('1h', 0),
                         'wind_speed': round(hour_data.get('wind_speed', 0) * 3.6, 2), 'fetched_at': datetime.now()})
                if 'alerts' in data:
                    for alert in data['alerts']: all_alerts_data.append(
                        {'city': city, 'event': alert.get('event', 'Alerta'),
                         'start_time': datetime.fromtimestamp(alert['start']),
                         'end_time': datetime.fromtimestamp(alert['end']), 'description': alert.get('description', ''),
                         'sender_name': alert.get('sender_name', 'Fuente desconocida'), 'fetched_at': datetime.now()})
                if 'daily' in data:
                    for day_data in data['daily']:
                        summary_text = day_data.get('summary', day_data['weather'][0].get('description', ''))
                        all_daily_data.append({"date": datetime.fromtimestamp(day_data['dt']).date(), "city": city,
                                               "temp": round(day_data['temp'].get('day', 0), 2),
                                               "feels_like": round(day_data['feels_like'].get('day', 0), 2),
                                               "humidity": day_data.get('humidity', 0),
                                               "weather_condition": summary_text.capitalize(),
                                               "main_condition": day_data['weather'][0].get('main', ''),
                                               "rain_probability": round(day_data.get('pop', 0) * 100, 2),
                                               "wind_speed": round(day_data.get('wind_speed', 0) * 3.6, 2),
                                               "fetched_at": datetime.now(), "total_rain_mm": day_data.get('rain', 0),
                                               "temp_max": round(day_data['temp'].get('max', 0), 2),
                                               "temp_min": round(day_data['temp'].get('min', 0), 2),
                                               "uvi": day_data.get('uvi', 0),
                                               "sunrise": datetime.fromtimestamp(day_data.get('sunrise', 0)),
                                               "sunset": datetime.fromtimestamp(day_data.get('sunset', 0))})
    db_conn = connect_db()
    if not db_conn: return False
    try:
        with db_conn.cursor() as cursor:
            print("Guardando datos en PostgreSQL...")
            for row in all_hourly_data: cursor.execute(
                "INSERT INTO hourly_weather_data (city, forecast_time, temp, feels_like, humidity, weather_condition, main_condition, rain_probability, rain_1h, wind_speed, fetched_at) VALUES (%(city)s, %(forecast_time)s, %(temp)s, %(feels_like)s, %(humidity)s, %(weather_condition)s, %(main_condition)s, %(rain_probability)s, %(rain_1h)s, %(wind_speed)s, %(fetched_at)s) ON CONFLICT (city, forecast_time) DO UPDATE SET temp=EXCLUDED.temp, feels_like=EXCLUDED.feels_like, humidity=EXCLUDED.humidity, weather_condition=EXCLUDED.weather_condition, main_condition=EXCLUDED.main_condition, rain_probability=EXCLUDED.rain_probability, rain_1h=EXCLUDED.rain_1h, wind_speed=EXCLUDED.wind_speed, fetched_at=EXCLUDED.fetched_at;",
                row)
            for row in all_alerts_data: cursor.execute(
                "INSERT INTO weather_alerts (city, event, start_time, end_time, description, sender_name, fetched_at) VALUES (%(city)s, %(event)s, %(start_time)s, %(end_time)s, %(description)s, %(sender_name)s, %(fetched_at)s) ON CONFLICT (city, event, start_time) DO NOTHING;",
                row)
            for row in all_daily_data: cursor.execute(
                "INSERT INTO weather_data (date, city, temp, feels_like, humidity, weather_condition, main_condition, rain_probability, wind_speed, fetched_at, total_rain_mm, temp_max, temp_min, uvi, sunrise, sunset) VALUES (%(date)s, %(city)s, %(temp)s, %(feels_like)s, %(humidity)s, %(weather_condition)s, %(main_condition)s, %(rain_probability)s, %(wind_speed)s, %(fetched_at)s, %(total_rain_mm)s, %(temp_max)s, %(temp_min)s, %(uvi)s, %(sunrise)s, %(sunset)s) ON CONFLICT (date, city) DO UPDATE SET temp=EXCLUDED.temp, feels_like=EXCLUDED.feels_like, humidity=EXCLUDED.humidity, weather_condition=EXCLUDED.weather_condition, main_condition=EXCLUDED.main_condition, rain_probability=EXCLUDED.rain_probability, wind_speed=EXCLUDED.wind_speed, fetched_at=EXCLUDED.fetched_at, total_rain_mm=EXCLUDED.total_rain_mm, temp_max=EXCLUDED.temp_max, temp_min=EXCLUDED.temp_min, uvi=EXCLUDED.uvi, sunrise=EXCLUDED.sunrise, sunset=EXCLUDED.sunset;",
                row)
        db_conn.commit()
        print(f"✅ PASO 1 completado en {round(time.time() - start_time, 2)} segundos.")
        return True
    except Exception as e:
        print(f"❌ Error al guardar en PostgreSQL: {e}")
        db_conn.rollback()
        return False
    finally:
        if db_conn: db_conn.close()


def upload_df_to_gsheet_full_refresh(worksheet, df):
    """
    Realiza un reemplazo completo de la hoja con los datos de un DataFrame.
    """
    print(f"Iniciando reemplazo completo para la hoja '{worksheet.title}'...")
    try:
        # Limpiar la hoja y subir los nuevos datos
        worksheet.clear()
        df = df.fillna('').astype(str)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')
        print(f"✅ Reemplazo completado para la hoja '{worksheet.title}'.")
    except Exception as e:
        print(f"❌ Error durante el reemplazo completo en la hoja '{worksheet.title}': {e}")


def extract_and_upload_data():
    """
    PASO 2: Extrae los datos de PostgreSQL y los sube a Google Sheets.
    """
    print("\n--- INICIANDO PASO 2: Subir Datos a Google Sheets (Método: Reemplazo Completo) ---")
    try:
        SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
        gspread_client = gspread.authorize(CREDS)
        spreadsheet = gspread_client.open(SHEET_NAME)
        print("✅ Conexión exitosa con Google Sheets.")
    except Exception as e:
        print(f"❌ Error fatal al conectar con Google Sheets: {e}")
        return

    db_conn = connect_db()
    if not db_conn: return

    try:
        # Para cada tabla, se extraen todos los datos y se reemplaza la hoja completamente

        # 1. Datos diarios ('weather_data')
        daily_worksheet = spreadsheet.worksheet(DAILY_SHEET_NAME)
        daily_df = pd.read_sql(f"SELECT * FROM weather_data ORDER BY city, date", db_conn)
        upload_df_to_gsheet_full_refresh(daily_worksheet, daily_df)

        # 2. Datos por hora ('hourly_weather_data')
        hourly_worksheet = spreadsheet.worksheet(HOURLY_SHEET_NAME)
        hourly_df = pd.read_sql(f"SELECT * FROM hourly_weather_data ORDER BY city, forecast_time", db_conn)
        upload_df_to_gsheet_full_refresh(hourly_worksheet, hourly_df)

        # 3. Alertas ('weather_alerts')
        alerts_worksheet = spreadsheet.worksheet(ALERTS_SHEET_NAME)
        alerts_df = pd.read_sql(f"SELECT * FROM weather_alerts ORDER BY city, start_time", db_conn)
        upload_df_to_gsheet_full_refresh(alerts_worksheet, alerts_df)

        # 4. Clusters ('city_team_cluster')
        cluster_worksheet = spreadsheet.worksheet(CLUSTER_SHEET_NAME)
        cluster_df = pd.read_sql("SELECT * FROM city_team_cluster ORDER BY city", db_conn)
        upload_df_to_gsheet_full_refresh(cluster_worksheet, cluster_df)

    except gspread.exceptions.WorksheetNotFound as e:
        # El error se maneja dentro de la función de subida, pero por si acaso
        print(f"❌ Error: La hoja '{e.sheet_name}' no existe. Por favor, créala manualmente.")
    except Exception as e:
        print(f"❌ Error durante la extracción y subida a Sheets: {e}")
    finally:
        if db_conn: db_conn.close()


# --- 3. EJECUCIÓN DEL PIPELINE ---

if __name__ == "__main__":
    print("🚀 Iniciando pipeline de actualización de datos del clima.")

    success = fetch_and_store_weather_data()

    if success:
        extract_and_upload_data()
        print("\n✨ Pipeline completado exitosamente.")
    else:
        print(
            "\n❌ Pipeline fallido. La base de datos no fue actualizada, por lo tanto no se subieron datos a Google Sheets.")
