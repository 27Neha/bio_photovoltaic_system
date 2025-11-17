import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app

print('OpenWeather key:', app.API_KEYS.get('openweathermap'))
print('Key valid:', getattr(app, 'OPENWEATHER_KEY_VALID', None))
res = app.fetch_weather_from_openweathermap('London')
print('Result:', res)
