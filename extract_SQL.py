import pandas as pd
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔹 Configuración de Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
client = gspread.authorize(CREDS)

# Abrir el Google Sheet
spreadsheet = client.open("Weather_Dashboard")

# 🔹 Configuración de PostgreSQL
PG_CONFIG = {
    "host": "localhost",
    "database": "weather_db",
    "user": "postgres",
    "password": "lazzeeli1"
}

# 📌 Función para extraer datos de `weather_data`
def extract_weather_data():
    conn = psycopg2.connect(**PG_CONFIG)
    query = "SELECT * FROM weather_data ORDER BY date, city"
    df = pd.read_sql(query, conn)
    conn.close()

    # 🔹 Convertir todas las fechas a string para evitar errores de serialización
    df = df.astype(str)

    # Subir datos a la hoja "Data"
    worksheet = spreadsheet.worksheet("Data")
    worksheet.clear()
    worksheet.append_row(df.columns.tolist())  # Agregar encabezados
    worksheet.append_rows(df.values.tolist())  # Agregar datos

    print("✅ Weather data exported to Google Sheets!")

# 📌 Función para extraer datos de `city_team_cluster`
def extract_city_team_cluster():
    conn = psycopg2.connect(**PG_CONFIG)
    query = "SELECT * FROM city_team_cluster ORDER BY city"
    df = pd.read_sql(query, conn)
    conn.close()

    # 🔹 Convertir todas las fechas a string para evitar errores
    df = df.astype(str)

    # Subir datos a la hoja "City_Team_Cluster"
    worksheet = spreadsheet.worksheet("City_Team_Cluster")
    worksheet.clear()
    worksheet.append_row(df.columns.tolist())  # Agregar encabezados
    worksheet.append_rows(df.values.tolist())  # Agregar datos

    print("✅ City-Team-Cluster data exported to Google Sheets!")

# 📌 Ejecutar ambas extracciones
if __name__ == "__main__":
    extract_weather_data()
    extract_city_team_cluster()
