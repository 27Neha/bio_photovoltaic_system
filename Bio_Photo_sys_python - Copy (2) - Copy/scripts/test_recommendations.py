import os
import sys
# Ensure parent project root is on sys.path so we can import `app` reliably
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import calculator

cities = ['London', 'Miami', 'Tokyo', 'New York', 'UnknownCity', 'Jalgaon', 'Mulshi', 'Los Angeles', 'Sydney']

for city in cities:
    weather = calculator.get_weather_data(city)
    recommendations = calculator.recommend_fruits(weather)
    print('City:', city)
    print('Weather:', weather)
    print('Top recommendations:')
    for r in recommendations:
        print(' -', r['name'], r['suitability_score'])
    print('\n' + '-'*40 + '\n')
