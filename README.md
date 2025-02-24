# 🌦️ Weather Dashboard

## 📌 Overview
The **Weather Dashboard** is a Streamlit web application designed for **Uber Data Analysts** to monitor weather conditions for various cities. It provides an overview of current weather conditions by **team (MX, CL, CO)** and **cluster**, as well as a **5-day detailed forecast** for selected cities.

## 🚀 Features
- **🌍 City Overview**: Displays the current weather for all cities within the selected **team and cluster**.
- **📊 Detailed Forecast**: Provides a **5-day forecast** for a selected city, including temperature trends and rain probability.
- **📅 Date Selection**: View forecasts for **specific dates**.
- **📈 Visual Trends**: Includes **interactive charts** for temperature and rain probability.


![image](https://github.com/user-attachments/assets/9b8d163d-0b7b-4a36-8d62-e81b4fcd873f)


![image](https://github.com/user-attachments/assets/099f441b-f811-468d-b3b1-533ea7d147b0)



## 🛠️ Tech Stack
- **Python** 🐍
- **Streamlit** 🎈
- **PostgreSQL** 🐘
- **Plotly** 📊
- **OpenWeather API** 🌤️

## 🔧 Installation
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/Weather_Dashboard.git
cd Weather_Dashboard
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure PostgreSQL Database
- Create a **PostgreSQL database** and update the connection details in `Weather_Dashboard.py`:
```python
PG_CONFIG = {
    "host": "your_host",
    "database": "your_db",
    "user": "your_user",
    "password": "your_password"
}
```
- Run the script to fetch and store weather data:
```bash
python weather_script.py
```

### 4️⃣ Run the Streamlit App
```bash
streamlit run Weather_Dashboard.py
```

## 🌍 Deployment on Streamlit Cloud
1. Push your project to GitHub.
2. Add a **requirements.txt** file:
```
streamlit
pandas
psycopg2
plotly
requests
```
3. Go to [Streamlit Cloud](https://share.streamlit.io/) and **deploy your app**.

## 📌 Usage
- **Choose a date** to view weather conditions.
- **Filter by team and cluster** to focus on specific cities.
- **Select a city** in the "Detailed Forecast" section to view **5-day trends**.


## 📞 Contact
For questions or improvements, contact me  eli.est.tgl@gmail.com

