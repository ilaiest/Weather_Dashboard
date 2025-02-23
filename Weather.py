import time
import requests
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
import concurrent.futures
from cities import cities

# Configuración de OpenWeather API
API_KEY = '28e3a39a2393ba8667b8d038ba3a9f83'  # 🔹 Reemplázalo con tu API Key de OpenWeather
BASE_URL = 'http://api.openweathermap.org/data/2.5/forecast'

# Configuración de PostgreSQL
PG_CONFIG = {
    "host": "localhost",
    "database": "weather_db",
    "user": "postgres",
    "password": "lazzeeli1"
}


# Función para conectar a PostgreSQL
def connect_db():
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    return conn, cursor


# Función para obtener datos del clima
def fetch_and_aggregate_forecast(city_data):
    city, (lat, lon, timezone) = city_data
    params = {'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        forecast_data = defaultdict(list)
        today = datetime.now().date()
        days = [today + timedelta(days=i) for i in range(5)]  # 5 días de pronóstico

        for forecast in data['list']:
            forecast_datetime = datetime.strptime(forecast['dt_txt'], "%Y-%m-%d %H:%M:%S")
            forecast_date = forecast_datetime.date()
            forecast_hour = forecast_datetime.strftime("%H:%M")

            if forecast_date in days:
                temp = forecast["main"]["temp"]
                feels_like = forecast["main"]["feels_like"]
                humidity = forecast["main"]["humidity"]
                rain = forecast.get("rain", {}).get("3h", 0)
                condition = forecast["weather"][0]["description"]
                main_condition = forecast["weather"][0]["main"]
                pop = forecast.get("pop", 0) * 100
                wind_speed = forecast["wind"]["speed"] * 3.6  # de m/s a km/h

                # ✅ Filtrar horarios entre las 6:00 AM y 9:00 PM para lluvia
                hour_int = int(forecast_hour.split(":")[0])
                if 6 <= hour_int <= 21 and rain > 0:
                    rain_label = f"{forecast_hour} ({round(rain, 1)}mm)"
                else:
                    rain_label = None

                # ✅ Acumular todos los horarios de lluvia en una lista y unirlos en una sola celda
                if rain_label:
                    existing_rain_hours = forecast_data[forecast_date][-1]["rain_hours"] if forecast_data[forecast_date] else ""
                    combined_rain_hours = f"{existing_rain_hours}, {rain_label}".strip(", ") if existing_rain_hours else rain_label
                else:
                    combined_rain_hours = None

                forecast_data[forecast_date].append({
                    "date": str(forecast_date), "city": city,
                    "temp": round(temp, 2), "feels_like": round(feels_like, 2),
                    "humidity": round(humidity, 2), "weather_condition": condition,
                    "main_condition": main_condition, "rain_probability": f"{round(pop)}%",
                    "rain_hours": combined_rain_hours, "wind_speed": round(wind_speed, 2),
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        return forecast_data
    else:
        print(f"❌ Error fetching data for {city}: {response.status_code}, {response.text}")
        return {}

# Función para almacenar datos en PostgreSQL con control de llamadas a la API
def fetch_and_store_weather_data():
    conn, cursor = connect_db()
    all_data = []

    city_data_list = [(city, (lat, lon, timezone)) for city, (lat, lon, timezone) in cities.items()]

    for i, city_data in enumerate(city_data_list):
        print(f"🌍 Consultando clima para: {city_data[0]} ({i + 1}/{len(city_data_list)})")

        forecast_data = fetch_and_aggregate_forecast(city_data)

        for date, rows in forecast_data.items():
            all_data.extend(rows)

        # 🔹 Si hemos hecho 50 consultas, esperamos 60 segundos antes de continuar
        if (i + 1) % 50 == 0:
            print("🕒 Pausando 60 segundos para evitar el límite de OpenWeather...")
            time.sleep(70)

    # Insertar datos en PostgreSQL
    for row in all_data:
        cursor.execute("""
            INSERT INTO weather_data (date, city, temp, feels_like, humidity, weather_condition, main_condition,
                                     rain_probability, rain_hours, wind_speed, fetched_at)
            VALUES (%(date)s, %(city)s, %(temp)s, %(feels_like)s, %(humidity)s, %(weather_condition)s, %(main_condition)s,
                    %(rain_probability)s, %(rain_hours)s, %(wind_speed)s, %(fetched_at)s)
            ON CONFLICT (date, city) DO UPDATE SET 
                temp=EXCLUDED.temp, feels_like=EXCLUDED.feels_like, humidity=EXCLUDED.humidity,
                weather_condition=EXCLUDED.weather_condition, main_condition=EXCLUDED.main_condition,
                rain_probability=EXCLUDED.rain_probability, rain_hours=EXCLUDED.rain_hours,
                wind_speed=EXCLUDED.wind_speed, fetched_at=EXCLUDED.fetched_at;
        """, row)

    conn.commit()
    conn.close()
    print("✅ Datos de clima almacenados en SQL.")


# Ejecutar script
if __name__ == "__main__":
    fetch_and_store_weather_data()
