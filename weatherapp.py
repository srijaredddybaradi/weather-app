import sys
import geocoder
import requests
from plyer import notification
from dotenv import load_dotenv
import os
from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFrame,
                             QLineEdit, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QPixmap, QPainter
load_dotenv()
weather_key = os.getenv("WEATHER_KEY")
api_key = os.getenv("API_KEY")
if not weather_key or not api_key:
    print("Error: Missing API keys. Check your .env file.")
    sys.exit(1)

condition_icon = {
    "clear": "icon/clear.png",
    "clouds": "icon/cloud.png",
    "rain": "icon/rain.png",
    "drizzle": "icon/drizzle.png",
    "sunny": "icon/sunny.png",
    "default": "icon/default.png"
}
playlist_links = {
    "clear": "https://open.spotify.com/playlist/6ZVbbDVtrnBfL2JekvvvOP?si=JChirUm_QxSi4mnZfx2LfQ&pi=FSCGht8nQkyWd",
    "sunny": "https://open.spotify.com/playlist/6ZVbbDVtrnBfL2JekvvvOP?si=JChirUm_QxSi4mnZfx2LfQ&pi=FSCGht8nQkyWd",
    "rain": "https://open.spotify.com/playlist/6YlOL4rhYfSLy7gbdOuYTj?si=iA3REPoHSQutX13sO6XV0w&pi=arvSGBb3Qa-8O",
    "cloud": "https://open.spotify.com/playlist/03nj4Todu6JffOLe68rEzY?si=Sb-88YLQTPmlYHrS3tLm7A&pi=H9qtSCmNQja9T",
    "default": "https://open.spotify.com/playlist/6u0XA0GbWDHW9h5mN2wx4v?si=aqz67tpwT8Gjl-bCgm8q8g&pi=yZgGQw2fTqKMs"
}


def get_weather_by_city(city, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if response.status_code != 200 or "main" not in data:
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None, None, None, None, None
        temp = data.get('main', {}).get('temp')
        condition = data.get('weather', [{}])[0].get('description')
        city_name = data.get('name', city)
        coord = data.get('coord', {})
        lat = coord.get('lat')
        lon = coord.get('lon')
        return temp, condition, city_name, lat, lon
    except Exception as e:
        print("City weather fetch error:", e)
        return None, None, None, None, None


def get_location():
    try:
        url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        city = data.get("city", "Unknown")
        return lat, lon, city
    except Exception as e:
        print("Location fetch error:", e)
        return None, None, None


def get_weather(lat, lon, api_key):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if response.status_code != 200 or "main" not in data:
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return None, None, None, None, None
        temp = data['main']['temp']
        condition = data['weather'][0]['description']
        city = data.get('name', 'unknown')
        # print("DEBUG Weather API URL:", url)
        # print("DEBUG Weather Response:", data)
        return temp, condition, city
    except Exception as e:
        print(f"Error getting location: {e}")
        return None, None, None


def recomendations(temp, condition):
    if 'rain' in condition.lower():
        return "carry an umbrella☔, raincoat, waterproof shoes👢,wear nylon or polyester\
              avoid heavy denim and cotton clothes!!"
    elif temp < 17:
        return "try carrying a jacket or sweater🧥, don't forget gloves🧤, socks🧦 and a hat\
              preferably woolen ones!!"
    elif 17 <= temp <= 29:
        return " carry a light jacket or scarf🧣 this is perfect weather to showcase your wardrobe!!"
    else:
        return "wear linen, cotton or any light fabrics, carry a hat,sunglasses🕶️ and dont forget your sunscreen😎, avoid black clothes!!"


def send_alert(title, msg, parent=None):
    notification.notify(title=title, message=msg, timeout=10)
    if parent is not None:
        QMessageBox.information(parent, title, msg)


def check_weather_alerts(lat, lon, city, parent=None):
    API_KEY = os.getenv("WEATHER_KEY")
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=alerts&units=metric&appid={API_KEY}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        res = res.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            print("Free API key does not support alerts, skipping.")
        else:
            print(f"Alert fetch error: {e}")
        return []
    except Exception as e:
        print(f"Other alert fetch error: {e}")
        return []

    if "minutely" in res:
        will_rain = any(m.get("precipitation", 0) >
                        0 for m in res["minutely"][:30])
        if will_rain:
            send_alert(
                "☔ Rain Alert", f"Rain expected in {city} within 30 min!,\ndont forget the umbrella☂️", parent)

    if "hourly" in res and len(res["hourly"]) > 0:
        next_hour = res["hourly"][0]
        cond_main = next_hour["weather"][0]["main"].lower()
        cond_id = next_hour["weather"][0].get("id", 0)
        wind_ms = float(next_hour.get("wind_speed", 0.0))

        if cond_main == "clear" or cond_id == 800:
            send_alert(
                "☀️ Sunny Alert", "your icecream gonna melt in seconds!\n😎 Apply sunscreen.", parent)

        if wind_ms > 7.0:
            send_alert(
                "💨 Wind Alert", f"Strong winds expected soon in {city}, watch ur hats!", parent)

    return res.get("alerts", [])


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Know Your Degree!! 🌥️")
        self.setGeometry(700, 300, 600, 550)
        self.setWindowIcon(QIcon("weather.jpg"))

        # --- Search Bar ---
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Enter city name...")
        self.search_input.setFont(QFont("Arial", 12))
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.15);
                border: 2px solid #FFD700;
                border-radius: 18px;
                padding: 0 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #FFA500;
                background-color: rgba(255,255,255,0.25);
            }
        """)

        self.search_btn = QPushButton("Search", self)
        self.search_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.search_btn.setMinimumHeight(40)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: black;
                border-radius: 18px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #FFC300;
            }
        """)

        self.search_input.returnPressed.connect(self.search_weather)
        self.search_btn.clicked.connect(self.search_weather)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(self.search_input, stretch=3)
        search_layout.addWidget(self.search_btn, stretch=1)

        # --- Weather Info ---
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(
            QPixmap("icon/default.png").scaled(80, 80, Qt.KeepAspectRatio))

        self.city_label = QLabel("—", self)
        self.city_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.city_label.setAlignment(Qt.AlignCenter)
        self.city_label.setStyleSheet("color: white;")

        self.temp_label = QLabel("—°C", self)
        self.temp_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setStyleSheet("color: white;")

        self.condition_label = QLabel("—", self)
        self.condition_label.setFont(QFont("Arial", 14))
        self.condition_label.setAlignment(Qt.AlignCenter)
        self.condition_label.setStyleSheet("color: white;")

        # --- Clothes Suggestion Box ---
        self.clothes_box = QFrame(self)
        self.clothes_box.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 12px;
            }
        """)
        self.clothes_label = QLabel("", self.clothes_box)
        self.clothes_label.setMinimumWidth(200)
        self.clothes_label.adjustSize()
        self.clothes_label.setFont(QFont("Arial", 12))
        self.clothes_label.setAlignment(Qt.AlignCenter)
        self.clothes_label.setWordWrap(True)
        self.clothes_label.setStyleSheet("color: white;")

        clothes_layout = QVBoxLayout(self.clothes_box)
        clothes_layout.addWidget(self.clothes_label)

        # --- Playlist Link ---
        self.playlist_label = QLabel("", self)
        self.playlist_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.playlist_label.setOpenExternalLinks(True)
        self.playlist_label.setAlignment(Qt.AlignCenter)
        self.playlist_label.setStyleSheet("""
            color: #FFD700;
            text-decoration: underline;
        """)

        # --- Main Layout ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.icon_label)
        main_layout.addWidget(self.city_label)
        main_layout.addWidget(self.temp_label)
        main_layout.addWidget(self.condition_label)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.clothes_box)
        main_layout.addWidget(self.playlist_label)

        self.setLayout(main_layout)

        # Call weather updater
        self.weather()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.weather)
        self.timer.start(600000)

    def search_weather(self):
        city = self.search_input.text().strip()
        if not city:
            QMessageBox.warning(self, "Input Error",
                                "Please enter a city name.")
            return

        temp, condition, city_name, lat, lon = get_weather_by_city(
            city, weather_key)
        if temp is None:
            QMessageBox.warning(self, "Error", "City not found or API error.")
            return

        self.update_weather_ui(temp, condition, city_name, lat, lon)

    def weather(self):
        lat, lon, ip_city = get_location()
        if lat and lon:
            temp, condition, city = get_weather(lat, lon, weather_key)
            if not city:
                city = ip_city

            self.update_weather_ui(temp, condition, city, lat, lon)

    def update_weather_ui(self, temp, condition, city, lat, lon):
        check_weather_alerts(lat, lon, city, self)

        if temp is not None and condition:
            self.city_label.setText(f"{city}")
            self.temp_label.setText(f"{temp}°C")
            self.condition_label.setText(condition.title())
            self.clothes_label.setText(
                f"👗 {recomendations(temp, condition)}")
            self.change_background(condition, temp)

            cond = (condition or "").lower()
            playlist_url = playlist_links.get("default")
            for key in playlist_links:
                if key in cond:
                    playlist_url = playlist_links[key]
                    break
            self.playlist_label.setText(
                f'<a href="{playlist_url}">🎵 Open Weather Playlist</a>')

            if "clear" in cond:
                icon_path = condition_icon["clear"]
            elif "cloud" in cond:
                icon_path = condition_icon["clouds"]
            elif "rain" in cond:
                icon_path = condition_icon["rain"]
            elif "drizzle" in cond:
                icon_path = condition_icon["drizzle"]
            elif "sun" in cond:
                icon_path = condition_icon["sunny"]
            else:
                icon_path = "icon/default.png"
            if not icon_path:
                icon_path = "icon/default.png"

            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                print(f"Image not found: {icon_path}")
                pixmap = QPixmap("icon/default.png")
            pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio)
            self.icon_label.setPixmap(pixmap)

    def change_background(self, condition, temp):
        palette = QPalette()
        if 'rain' in condition.lower():
            bg_color = QColor('#878282')
        elif 'storm' in condition.lower():
            bg_color = QColor("#39393A")
        else:
            if temp <= 10:
                bg_color = QColor('#D0F4F5')
            elif 10 < temp <= 20:
                bg_color = QColor('#D7F7C9')
            elif 20 < temp <= 29:
                bg_color = QColor('#FFECA1')
            elif 29 < temp <= 40:
                bg_color = QColor('#FF9E00')
            else:
                bg_color = QColor("#E12022")

        palette.setColor(QPalette.Window, bg_color)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

        brightness = (bg_color.red() * 0.299 +
                      bg_color.green() * 0.587 +
                      bg_color.blue() * 0.114)
        text_color = "black" if brightness > 186 else "white"

        for label in [self.city_label, self.temp_label, self.condition_label, self.clothes_label, self.playlist_label]:
            label.setStyleSheet(f"color: {text_color};")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
