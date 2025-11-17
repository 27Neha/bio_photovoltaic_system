# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify
import requests
import json
import math
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

app = Flask(__name__)

# API Configuration
API_KEYS = {
    'openweathermap': os.getenv('OPENWEATHER_API_KEY', 'demo_key'),
    'weatherapi': os.getenv('WEATHERAPI_KEY', 'demo_key'),
    'currency': os.getenv('EXCHANGERATE_API_KEY', 'demo_key')
}

# Load environment variables from config.env if available
env_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Overwrite API_KEYS from env (so config.env values are used)
API_KEYS['openweathermap'] = os.getenv('OPENWEATHER_API_KEY', API_KEYS['openweathermap'])
API_KEYS['weatherapi'] = os.getenv('WEATHERAPI_KEY', API_KEYS['weatherapi'])
API_KEYS['currency'] = os.getenv('EXCHANGERATE_API_KEY', API_KEYS['currency'])

# Define whether to use mock data
env_use_mock = os.getenv('USE_MOCK_DATA')
if env_use_mock is None:
    # If user didn't explicitly set USE_MOCK_DATA, prefer live if API keys are present
    if (API_KEYS.get('openweathermap') and API_KEYS['openweathermap'] != 'demo_key') or (API_KEYS.get('weatherapi') and API_KEYS['weatherapi'] != 'demo_key'):
        USE_MOCK_DATA = False
    else:
        USE_MOCK_DATA = True
else:
    USE_MOCK_DATA = env_use_mock.lower() not in ('0', 'false', 'no')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bio-photo')

# Validate whether API keys are present and valid; keep fallbacks
OPENWEATHER_KEY_VALID = False
WEATHERAPI_KEY_VALID = False


def validate_openweather_key(test_city='London'):
    """Validate OpenWeather key by geocoding a known city.
    Returns True if valid; False otherwise.
    """
    key = API_KEYS.get('openweathermap')
    if not key or key == 'demo_key':
        return False
    try:
        geo_url = f'https://api.openweathermap.org/geo/1.0/direct?q={requests.utils.quote(test_city)}&limit=1&appid={key}'
        r = requests.get(geo_url, timeout=6)
        if r.status_code != 200:
            logger.warning('OpenWeather geocode validation failed: %s', r.text)
            return False
        data = r.json()
        if not data:
            return False
        lat = data[0]['lat']
        lon = data[0]['lon']
        # Try the simple current weather endpoint (more widely available than OneCall for some accounts)
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={key}'
        r2 = requests.get(weather_url, timeout=6)
        if r2.status_code != 200:
            logger.warning('OpenWeather current weather validation call failed: %s', r2.text)
            return False
        return True
    except Exception:
        logger.exception('Error when validating OpenWeather key')
        return False


def validate_weatherapi_key(test_city='London'):
    key = API_KEYS.get('weatherapi')
    if not key or key == 'demo_key':
        return False
    try:
        url = f'https://api.weatherapi.com/v1/current.json?key={key}&q={requests.utils.quote(test_city)}&aqi=no'
        r = requests.get(url, timeout=6)
        if r.status_code != 200:
            logger.warning('WeatherAPI key validation failed: %s', r.text)
            return False
        data = r.json()
        return 'current' in data and 'location' in data
    except Exception:
        logger.exception('Error when validating WeatherAPI key')
        return False


def validate_api_keys():
    global OPENWEATHER_KEY_VALID, WEATHERAPI_KEY_VALID, USE_MOCK_DATA
    try:
        OPENWEATHER_KEY_VALID = validate_openweather_key()
        WEATHERAPI_KEY_VALID = validate_weatherapi_key()
        logger.info('API Key Validation: OpenWeather=%s WeatherAPI=%s', OPENWEATHER_KEY_VALID, WEATHERAPI_KEY_VALID)
        # Prefers live provider if at least one provider is valid and USE_MOCK_DATA was not explicitly set to true
        if OPENWEATHER_KEY_VALID or WEATHERAPI_KEY_VALID:
            if os.getenv('USE_MOCK_DATA') is None:
                USE_MOCK_DATA = False
        else:
            USE_MOCK_DATA = True
    except Exception:
        logger.exception('Error during API keys validation')


validate_api_keys()


def fetch_weather_from_openweathermap(city):
    key = API_KEYS.get('openweathermap')
    if not key or key == 'demo_key':
        logger.debug('No OpenWeather API key found; skipping OpenWeather')
        return None
    try:
        # Geocode
        geo_url = f'https://api.openweathermap.org/geo/1.0/direct?q={requests.utils.quote(city)}&limit=1&appid={key}'
        g = requests.get(geo_url, timeout=8)
        if g.status_code != 200:
            logger.warning('OpenWeather geocode failed: %s', g.text)
            return None
        geo = g.json()
        if not geo:
            return None
        lat = geo[0]['lat']
        lon = geo[0]['lon']
        country = geo[0].get('country')
        # Prefer OneCall if available — gives uv index and extra info — but some accounts may not have OneCall access
        onecall_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&units=metric&appid={key}'
        r1 = requests.get(onecall_url, timeout=8)
        if r1.status_code == 200:
            current = r1.json().get('current', {})
            temp = current.get('temp')
            humidity = current.get('humidity')
            cloud_cover = current.get('clouds')
            uv = current.get('uvi', 0)
            light_intensity = int(uv * 10000)
        else:
            # Fallback to the current weather endpoint which is commonly available and returns at least temp/humidity/clouds
            weather_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={key}'
            r2 = requests.get(weather_url, timeout=8)
            if r2.status_code != 200:
                logger.warning('OpenWeather weather endpoint failed for %s: %s', city, r2.text)
                return None
            current = r2.json()
            temp = current.get('main', {}).get('temp')
            humidity = current.get('main', {}).get('humidity')
            cloud_cover = current.get('clouds', {}).get('all')
            # UV not available in this endpoint; set to None and compute a rough light intensity using cloud cover
            uv = None
            if cloud_cover is not None:
                light_intensity = int(max(1000, 100000 - (cloud_cover or 0) * 1000))
            else:
                light_intensity = None
        # simple climate guess based on latitude
        if abs(lat) < 23:
            climate_zone = 'tropical'
        elif 23 <= abs(lat) <= 40:
            climate_zone = 'subtropical'
        else:
            climate_zone = 'temperate'
        data = {
            'temperature': temp,
            'humidity': humidity,
            'cloud_cover': cloud_cover,
            'uv_index': uv,
            'light_intensity': light_intensity,
            'climate_zone': climate_zone,
            'country': country
            , 'provider': 'openweathermap'
        }
        logger.info("OpenWeather returned data for %s: %s", city, data)
        return data
    except Exception as e:
        logger.exception('OpenWeather fetch error')
        return None


def fetch_weather_from_weatherapi(city):
    key = API_KEYS.get('weatherapi')
    if not key or key == 'demo_key':
        logger.debug('No WeatherAPI key found; skipping WeatherAPI')
        return None
    try:
        url = f'https://api.weatherapi.com/v1/current.json?key={key}&q={requests.utils.quote(city)}&aqi=no'
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            logger.warning('WeatherAPI request failed: %s', r.text)
            return None
        j = r.json()
        loc = j.get('location', {})
        current = j.get('current', {})
        lat = loc.get('lat')
        if lat is None:
            climate_zone = 'temperate'
        else:
            if abs(lat) < 23:
                climate_zone = 'tropical'
            elif 23 <= abs(lat) <= 40:
                climate_zone = 'subtropical'
            else:
                climate_zone = 'temperate'
        uv = current.get('uv')  # let it be None if not present
        data = {
            'temperature': current.get('temp_c'),
            'humidity': current.get('humidity'),
            'cloud_cover': current.get('cloud'),
            'uv_index': uv,
            'light_intensity': int(uv * 10000) if uv is not None else None,
            'climate_zone': climate_zone,
            'country': loc.get('country'),
            'provider': 'weatherapi'
        }
        logger.info('WeatherAPI returned data for %s: %s', city, data)
        return data
    except Exception as e:
        logger.exception('WeatherAPI fetch error')
        return None

# Fruit Database (Sample Data - In production, this would come from APIs)
FRUIT_DATABASE = {
    'beetroot': {
        'name': 'Beetroot',
        'scientific_name': 'Beta vulgaris',
        'ph_level': 5.3,
        'acidity': 'medium',
        'conductivity': 0.8,
        'redox_potential': 0.75,
        'efficiency': 0.85,
        'cost_per_kg': 1.20,
        'juice_required_per_sqft': 175,
        'resin_ratio': 0.5,
        'power_density_per_sqft': 1.05,
        'climate_specialization': 'cloudy',
        'low_light_efficiency': 0.95,
        'high_uv_efficiency': 0.65,
        'photosynthetic_pigments': {
            'chlorophyll': 12.5,
            'carotenoids': 8.2,
            'anthocyanins': 15.8,
            'betalains': 45.3,
            'flavonoids': 22.1
        },
        'activation_threshold': {
            'uv_index': 2,
            'light_intensity': 2000,
            'cloud_cover_max': 80
        },
        'regional_optimization': {
            'best_climate_zones': ['temperate', 'continental'],
            'seasonal_performance': {'spring': 0.9, 'summer': 0.85, 'autumn': 0.95, 'winter': 0.7},
            'humidity_tolerance': 70,
            'temperature_range': {'min': 5, 'max': 25}
        },
        'uv_triggered_generation': True,
        'operational_lifespan': 18,
        'degradation_rate_monthly': 2.0,
        'environmental_adaptation': 0.9,
        'ion_conductivity': 0.45,
        'availability_by_region': {'europe': 'high', 'north_america': 'medium', 'asia': 'medium'},
        'seasonal_availability': ['autumn', 'winter'],
        'panel_replacement_interval': 18,
        'resin_curing_time': 4,
        'installation_complexity': 'simple'
    },
    'orange': {
        'name': 'Orange',
        'scientific_name': 'Citrus × sinensis',
        'ph_level': 3.5,
        'acidity': 'high',
        'conductivity': 1.2,
        'redox_potential': 0.92,
        'efficiency': 0.78,
        'cost_per_kg': 1.80,
        'juice_required_per_sqft': 200,
        'resin_ratio': 0.6,
        'power_density_per_sqft': 1.25,
        'climate_specialization': 'sunny',
        'low_light_efficiency': 0.45,
        'high_uv_efficiency': 0.95,
        'photosynthetic_pigments': {
            'chlorophyll': 8.3,
            'carotenoids': 35.2,
            'anthocyanins': 2.1,
            'betalains': 0.0,
            'flavonoids': 28.5
        },
        'activation_threshold': {
            'uv_index': 4,
            'light_intensity': 5000,
            'cloud_cover_max': 40
        },
        'regional_optimization': {
            'best_climate_zones': ['tropical', 'subtropical', 'mediterranean'],
            'seasonal_performance': {'spring': 0.8, 'summer': 0.95, 'autumn': 0.85, 'winter': 0.6},
            'humidity_tolerance': 85,
            'temperature_range': {'min': 15, 'max': 35}
        },
        'uv_triggered_generation': True,
        'operational_lifespan': 15,
        'degradation_rate_monthly': 2.5,
        'environmental_adaptation': 0.85,
        'ion_conductivity': 0.68,
        'availability_by_region': {'global': 'high'},
        'seasonal_availability': ['winter', 'spring'],
        'panel_replacement_interval': 15,
        'resin_curing_time': 6,
        'installation_complexity': 'simple'
    },
    'blueberry': {
        'name': 'Blueberry',
        'scientific_name': 'Vaccinium corymbosum',
        'ph_level': 3.8,
        'acidity': 'medium',
        'conductivity': 0.95,
        'redox_potential': 0.82,
        'efficiency': 0.72,
        'cost_per_kg': 8.50,
        'juice_required_per_sqft': 190,
        'resin_ratio': 0.55,
        'power_density_per_sqft': 0.95,
        'climate_specialization': 'cloudy',
        'low_light_efficiency': 0.88,
        'high_uv_efficiency': 0.58,
        'photosynthetic_pigments': {
            'chlorophyll': 10.2,
            'carotenoids': 12.8,
            'anthocyanins': 52.4,
            'betalains': 0.0,
            'flavonoids': 45.3
        },
        'activation_threshold': {
            'uv_index': 2,
            'light_intensity': 2500,
            'cloud_cover_max': 75
        },
        'regional_optimization': {
            'best_climate_zones': ['temperate', 'continental'],
            'seasonal_performance': {'spring': 0.75, 'summer': 0.9, 'autumn': 0.85, 'winter': 0.5},
            'humidity_tolerance': 75,
            'temperature_range': {'min': 10, 'max': 28}
        },
        'uv_triggered_generation': True,
        'operational_lifespan': 16,
        'degradation_rate_monthly': 2.2,
        'environmental_adaptation': 0.82,
        'ion_conductivity': 0.52,
        'availability_by_region': {'north_america': 'high', 'europe': 'medium', 'asia': 'low'},
        'seasonal_availability': ['summer'],
        'panel_replacement_interval': 16,
        'resin_curing_time': 5,
        'installation_complexity': 'moderate'
    }
    ,
    'mango': {
        'name': 'Mango',
        'scientific_name': 'Mangifera indica',
        'ph_level': 5.2,
        'acidity': 'low',
        'conductivity': 0.9,
        'redox_potential': 0.8,
        'efficiency': 0.9,
        'cost_per_kg': 2.0,
        'juice_required_per_sqft': 250,
        'resin_ratio': 0.6,
        'power_density_per_sqft': 1.5,
        'climate_specialization': 'tropical',
        'low_light_efficiency': 0.5,
        'high_uv_efficiency': 0.98,
        'activation_threshold': {'uv_index': 6, 'light_intensity': 60000, 'cloud_cover_max': 30},
        'regional_optimization': {'best_climate_zones': ['tropical', 'subtropical'], 'temperature_range': {'min': 20, 'max': 36}},
        'uv_triggered_generation': True,
        'operational_lifespan': 12,
        'resin_curing_time': 7,
        'installation_complexity': 'moderate',
        'availability_by_region': {'asia': 'high','south_america':'high'},
        'seasonal_availability': ['spring','summer']
    },
    'banana': {
        'name': 'Banana',
        'scientific_name': 'Musa acuminata',
        'ph_level': 5.0,
        'acidity': 'low',
        'conductivity': 0.9,
        'redox_potential': 0.79,
        'efficiency': 0.88,
        'cost_per_kg': 1.5,
        'juice_required_per_sqft': 200,
        'resin_ratio': 0.5,
        'power_density_per_sqft': 1.35,
        'climate_specialization': 'tropical',
        'low_light_efficiency': 0.6,
        'high_uv_efficiency': 0.92,
        'activation_threshold': {'uv_index': 5, 'light_intensity': 40000, 'cloud_cover_max': 40},
        'regional_optimization': {'best_climate_zones': ['tropical'], 'temperature_range': {'min': 18, 'max': 35}},
        'uv_triggered_generation': True,
        'operational_lifespan': 12,
        'resin_curing_time': 5,
        'installation_complexity': 'simple',
        'availability_by_region': {'asia': 'high', 'africa': 'high'},
        'seasonal_availability': ['all']
    },
    'apple': {
        'name': 'Apple',
        'scientific_name': 'Malus domestica',
        'ph_level': 3.7,
        'acidity': 'high',
        'conductivity': 0.9,
        'redox_potential': 0.85,
        'efficiency': 0.8,
        'cost_per_kg': 2.2,
        'juice_required_per_sqft': 180,
        'resin_ratio': 0.5,
        'power_density_per_sqft': 1.0,
        'climate_specialization': 'temperate',
        'low_light_efficiency': 0.9,
        'high_uv_efficiency': 0.7,
        'activation_threshold': {'uv_index': 2, 'light_intensity': 3000, 'cloud_cover_max': 70},
        'regional_optimization': {'best_climate_zones': ['temperate','continental'], 'temperature_range': {'min': 4, 'max': 24}},
        'uv_triggered_generation': True,
        'operational_lifespan': 20,
        'resin_curing_time': 6,
        'installation_complexity': 'moderate',
        'availability_by_region': {'europe': 'high','north_america':'high'},
        'seasonal_availability': ['autumn']
    },
    'grape': {
        'name': 'Grape',
        'scientific_name': 'Vitis vinifera',
        'ph_level': 3.4,
        'acidity': 'medium',
        'conductivity': 0.85,
        'redox_potential': 0.8,
        'efficiency': 0.8,
        'cost_per_kg': 2.4,
        'juice_required_per_sqft': 160,
        'resin_ratio': 0.5,
        'power_density_per_sqft': 1.1,
        'climate_specialization': 'mediterranean',
        'low_light_efficiency': 0.6,
        'high_uv_efficiency': 0.95,
        'activation_threshold': {'uv_index': 4, 'light_intensity': 45000, 'cloud_cover_max': 40},
        'regional_optimization': {'best_climate_zones': ['mediterranean','subtropical'], 'temperature_range': {'min': 12, 'max': 32}},
        'uv_triggered_generation': True,
        'operational_lifespan': 18,
        'resin_curing_time': 6,
        'installation_complexity': 'complex',
        'availability_by_region': {'europe': 'high','north_america':'high'},
        'seasonal_availability': ['summer']
    }
}

# Device Categories Database
DEVICE_CATEGORIES = {
    'small': {
        'name': 'Small Devices (<5W)',
        'power_range': (1, 5),
        'examples': [
            {'name': 'LED Light Bulb', 'power': 3, 'description': 'Energy-efficient lighting'},
            {'name': 'Phone Charger', 'power': 5, 'description': 'Smartphone charging'},
            {'name': 'USB Fan', 'power': 4, 'description': 'Personal cooling'},
            {'name': 'Bluetooth Speaker', 'power': 2, 'description': 'Portable audio'},
            {'name': 'Digital Clock', 'power': 1, 'description': 'Time display'}
        ],
        'panel_size_range': (0.5, 2),
        'daily_runtime_hours': 8
    },
    'medium': {
        'name': 'Medium Devices (5-50W)',
        'power_range': (5, 50),
        'examples': [
            {'name': 'Laptop Charger', 'power': 45, 'description': 'Computer power supply'},
            {'name': 'Tablet Charger', 'power': 25, 'description': 'Tablet charging'},
            {'name': 'Small Router', 'power': 15, 'description': 'Internet connectivity'},
            {'name': 'LED TV Strip', 'power': 30, 'description': 'Ambient lighting'},
            {'name': 'Webcam', 'power': 8, 'description': 'Video conferencing'}
        ],
        'panel_size_range': (2, 10),
        'daily_runtime_hours': 6
    },
    'large': {
        'name': 'Large Devices (50-500W)',
        'power_range': (50, 500),
        'examples': [
            {'name': 'Desktop Computer', 'power': 300, 'description': 'Workstation/gaming PC'},
            {'name': 'Gaming Console', 'power': 200, 'description': 'Entertainment system'},
            {'name': 'Mini Fridge', 'power': 150, 'description': 'Compact cooling'},
            {'name': 'Large Monitor', 'power': 60, 'description': 'Display screen'},
            {'name': 'Kitchen Appliance', 'power': 400, 'description': 'Small cooking device'}
        ],
        'panel_size_range': (10, 50),
        'daily_runtime_hours': 4
    }
}

class BiophotovoltaicCalculator:
    def __init__(self):
        self.weather_data_cache = {}

    def country_to_region(self, country_code):
        """Map a country code (ISO2) to a region key used in FRUIT_DATABASE availability_by_region.
        Very simple mapping for major countries; falls back to 'global'."""
        if not country_code:
            return None
        code = country_code.upper()
        europe = {'GB','FR','DE','IT','ES','NL','BE','SE','CH','NO','DK','IE','PL'}
        north_america = {'US','CA','MX'}
        asia = {'IN','CN','JP','SG','TH','MY','ID','VN','PH','PK','BD','KR'}
        africa = {'ZA','NG','EG','MA','KE'}
        south_america = {'BR','AR','CL','PE','CO'}
        oceania = {'AU','NZ','FJ'}
        if code in europe:
            return 'europe'
        if code in north_america:
            return 'north_america'
        if code in asia:
            return 'asia'
        if code in africa:
            return 'africa'
        if code in south_america:
            return 'south_america'
        if code in oceania:
            return 'oceania'
        return 'global'
    
    def get_weather_data(self, city, force_mock=None):
        """Get weather data for a city (mock or live)
        If USE_MOCK_DATA is false, attempt to fetch from configured weather APIs (OpenWeatherMap then WeatherAPI).
        """
        # Attempt to use cached data first
        city_key = city.lower() if isinstance(city, str) else str(city)
        # Use separate cache keys for mock vs live requests so forced overrides are respected
        cache_key = f"{city_key}:mock" if force_mock else f"{city_key}:live"
        if cache_key in self.weather_data_cache:
            return self.weather_data_cache[cache_key]

        # In production, this would call OpenWeatherMap or another weather API
        mock_weather_data = {
            'london': {
                'temperature': 15,
                'humidity': 75,
                'cloud_cover': 68,
                'uv_index': 2,
                'light_intensity': 5000,
                'climate_zone': 'temperate',
                'country': 'UK'
            },
            'miami': {
                'temperature': 28,
                'humidity': 80,
                'cloud_cover': 25,
                'uv_index': 8,
                'light_intensity': 85000,
                'climate_zone': 'tropical',
                'country': 'USA'
            },
            'tokyo': {
                'temperature': 18,
                'humidity': 70,
                'cloud_cover': 45,
                'uv_index': 5,
                'light_intensity': 65000,
                'climate_zone': 'temperate',
                'country': 'Japan'
            }
            ,
            'jalgaon': {
                'temperature': 32,
                'humidity': 55,
                'cloud_cover': 40,
                'uv_index': 9,
                'light_intensity': 90000,
                'climate_zone': 'tropical',
                'country': 'India',
                'provider': 'mock'
            },
            'mulshi': {
                'temperature': 21,
                'humidity': 65,
                'cloud_cover': 50,
                'uv_index': 4,
                'light_intensity': 50000,
                'climate_zone': 'temperate',
                'country': 'India',
                'provider': 'mock'
            }
        }
        
        # If the environment variable indicates we should use live data, try the provider(s)
        # Determine whether to use mock data for this request
        if force_mock is None:
            use_mock = USE_MOCK_DATA
        else:
            use_mock = force_mock

        if not use_mock:
            # Preferred provider: OpenWeatherMap
            data = fetch_weather_from_openweathermap(city)
            if data:
                # Ensure provider is set
                if 'provider' not in data:
                    data['provider'] = 'openweathermap'
                self.weather_data_cache[cache_key] = data
                return data
            # Fallback provider: WeatherAPI
            data = fetch_weather_from_weatherapi(city)
            if data:
                if 'provider' not in data:
                    data['provider'] = 'weatherapi'
                self.weather_data_cache[cache_key] = data
                return data

        city_lower = city.lower()
        if city_lower in mock_weather_data:
            self.weather_data_cache[cache_key] = mock_weather_data[city_lower]
            return mock_weather_data[city_lower]
        else:
            # Default data for unknown cities
            default = {
                'temperature': 20,
                'humidity': 65,
                'cloud_cover': 50,
                'uv_index': 4,
                'light_intensity': 50000,
                'climate_zone': 'temperate',
                'country': 'Unknown',
                'provider': 'mock'
            }
            self.weather_data_cache[cache_key] = default
            return default
    
    def calculate_fruit_suitability(self, fruit, weather_data):
        """Calculate how suitable a fruit is for given weather conditions"""
        fruit_data = FRUIT_DATABASE[fruit]
        score = 0
        
        # Determine region from country code if present
        country = weather_data.get('country') if weather_data else None
        region = self.country_to_region(country) if country else None

        # Climate specialization matching
        cloud_cover = weather_data.get('cloud_cover') if weather_data else None
        uv_index_val = weather_data.get('uv_index') if weather_data else None
        if cloud_cover is not None and cloud_cover > 60 and fruit_data['climate_specialization'] == 'cloudy':
            score += 30
        elif uv_index_val is not None and uv_index_val > 5 and fruit_data['climate_specialization'] == 'sunny':
            score += 30
        
        # Light intensity matching
        light_intensity = weather_data.get('light_intensity') if weather_data else None
        if light_intensity is None:
            # Can't judge; use a neutral baseline
            avg_eff = (fruit_data['low_light_efficiency'] + fruit_data['high_uv_efficiency']) / 2
            score += avg_eff * 25
        else:
            if light_intensity < 10000:  # Low light conditions
                score += fruit_data['low_light_efficiency'] * 25
            else:  # High light conditions
                score += fruit_data['high_uv_efficiency'] * 25
        
        # UV index matching
        # UV index matching (if UV index is available)
        if uv_index_val is None:
            uv_match = 1.0
        else:
            uv_match = 1 - abs(uv_index_val - fruit_data['activation_threshold']['uv_index']) / 10
        score += uv_match * 20
        
        # Temperature matching
        temp_range = fruit_data['regional_optimization']['temperature_range']
        optimal_temp = (temp_range['min'] + temp_range['max']) / 2
        temp_diff = abs(weather_data['temperature'] - optimal_temp)
        temp_score = max(0, 1 - temp_diff / 20)
        score += temp_score * 15
        
        # Region availability factor (prefer fruits more available in the region)
        region_score = 0
        if region:
            av = fruit_data.get('availability_by_region', {})
            region_av = av.get(region) or av.get('global')
            if region_av == 'high':
                region_score += 10
            elif region_av == 'medium':
                region_score += 5
        score += region_score

        # Cost factor (lower cost = higher score)
        cost_factor = max(0.1, 1 - (fruit_data['cost_per_kg'] / 10))
        score += cost_factor * 10
        
        return min(100, score)
    
    def recommend_fruits(self, weather_data, top_n=5):
        """Get top fruit recommendations based on weather conditions"""
        scores = {}
        
        for fruit in FRUIT_DATABASE:
            scores[fruit] = self.calculate_fruit_suitability(fruit, weather_data)
        
        # Sort by score descending
        sorted_fruits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for fruit, score in sorted_fruits[:top_n]:
            fruit_data = FRUIT_DATABASE[fruit].copy()
            fruit_data['suitability_score'] = round(score, 1)
            recommendations.append(fruit_data)
        
        return recommendations
    
    def calculate_power_output(self, fruit, panel_size, weather_data):
        """Calculate power output for given parameters"""
        fruit_data = FRUIT_DATABASE[fruit]
        
        # Base power density
        base_power = fruit_data['power_density_per_sqft'] * panel_size
        
        # Weather adjustments
        cloud_cover = weather_data.get('cloud_cover') if weather_data else None
        if cloud_cover is not None and cloud_cover > 60:  # Cloudy conditions
            weather_factor = fruit_data['low_light_efficiency']
        else:  # Sunny conditions or unknown
            weather_factor = fruit_data['high_uv_efficiency']
        
        # UV activation check
        uv_index_val = weather_data.get('uv_index') if weather_data else None
        if uv_index_val is None:
            activation_factor = 1.0
        elif uv_index_val < fruit_data['activation_threshold']['uv_index']:
            activation_factor = 0.3  # Reduced output if below UV threshold
        else:
            activation_factor = 1.0
        
        # Light intensity factor
        if weather_data.get('light_intensity') is None:
            light_factor = 1.0
        else:
            light_factor = min(1.0, weather_data['light_intensity'] / 100000)
        
        calculated_power = base_power * weather_factor * activation_factor * light_factor
        
        return {
            'current_power': round(calculated_power, 2),
            'daily_energy': round(calculated_power * 8, 2),  # 8 hours of generation
            'monthly_energy': round(calculated_power * 8 * 30, 2),
            'weather_factor': round(weather_factor, 2),
            'activation_status': 'ACTIVE' if activation_factor > 0.5 else 'LOW',
            'light_factor': round(light_factor, 2)
        }
    
    def calculate_installation_requirements(self, fruit, panel_size):
        """Calculate installation requirements"""
        fruit_data = FRUIT_DATABASE[fruit]
        
        juice_required = fruit_data['juice_required_per_sqft'] * panel_size
        resin_required = juice_required * fruit_data['resin_ratio']
        
        installation_cost = (juice_required / 1000) * fruit_data['cost_per_kg'] + (resin_required / 1000) * 5  # $5 per liter resin
        
        return {
            'juice_required_ml': round(juice_required),
            'resin_required_ml': round(resin_required),
            'installation_cost': round(installation_cost, 2),
            'curing_time_hours': fruit_data['resin_curing_time'],
            'complexity': fruit_data['installation_complexity'],
            'lifespan_months': fruit_data['operational_lifespan']
        }
    
    def get_compatible_devices(self, power_output, category=None):
        """Get list of compatible devices for given power output"""
        compatible = []
        
        for cat_name, cat_data in DEVICE_CATEGORIES.items():
            if category and category != cat_name:
                continue
                
            for device in cat_data['examples']:
                if device['power'] <= power_output:
                    runtime_hours = (power_output / device['power']) * cat_data['daily_runtime_hours']
                    device_copy = device.copy()
                    device_copy['runtime_hours'] = round(runtime_hours, 1)
                    device_copy['category'] = cat_name
                    compatible.append(device_copy)
        
        # Sort by power requirement (ascending)
        compatible.sort(key=lambda x: x['power'])
        return compatible

# Initialize calculator
calculator = BiophotovoltaicCalculator()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/city-input')
def city_input():
    return render_template('city_input.html')

@app.route('/recommendations')
@app.route('/recommendations/<city>')
def recommendations(city=None):
    # Allow city from path or query parameter for both server-rendered and SPA usage
    if not city:
        city = request.args.get('city', 'London')
    # allow mock override via query param `mock=true/false`
    mock_param = request.args.get('mock')
    if mock_param is None:
        use_mock = USE_MOCK_DATA
    else:
        use_mock = mock_param.lower() in ('1', 'true', 'yes')
    weather_data = calculator.get_weather_data(city, force_mock=use_mock)
    logger.info('recommendations: city=%s use_mock=%s provider=%s', city, use_mock, weather_data.get('provider'))
    fruit_recommendations = calculator.recommend_fruits(weather_data)
    
    return render_template('recommendations.html', 
                         city=city,
                         weather=weather_data,
                         fruits=fruit_recommendations)

@app.route('/calculator')
@app.route('/calculator/<city>')
def system_calculator(city=None):
    # Allow city in path or query; other parameters are query params
    if not city:
        city = request.args.get('city', 'London')
    fruit = request.args.get('fruit')
    panel_size = float(request.args.get('panel_size', 2))
    device_category = request.args.get('device_category', 'small')
    
    mock_param = request.args.get('mock')
    if mock_param is None:
        use_mock = USE_MOCK_DATA
    else:
        use_mock = mock_param.lower() in ('1', 'true', 'yes')
    weather_data = calculator.get_weather_data(city, force_mock=use_mock)
    # If a fruit is not provided, select the top recommended fruit for the city
    if not fruit:
        try:
            recs = calculator.recommend_fruits(weather_data)
            if recs and len(recs) > 0:
                fruit = recs[0]['name'].lower()
            else:
                fruit = 'beetroot'
        except Exception:
            fruit = 'beetroot'
    logger.info('calculator: city=%s fruit=%s use_mock=%s provider=%s', city, fruit, use_mock, weather_data.get('provider'))
    power_output = calculator.calculate_power_output(fruit, panel_size, weather_data)
    installation = calculator.calculate_installation_requirements(fruit, panel_size)
    compatible_devices = calculator.get_compatible_devices(power_output['current_power'], device_category)
    
    return render_template('calculator.html',
                         city=city,
                         fruit=FRUIT_DATABASE[fruit],
                         panel_size=panel_size,
                         device_category=device_category,
                         weather=weather_data,
                         power=power_output,
                         installation=installation,
                         devices=compatible_devices,
                         device_categories=DEVICE_CATEGORIES)

@app.route('/api/recommendations/<city>')
def api_recommendations(city):
    # allow per-request override of mock vs live via ?mock=true/false
    mock_param = request.args.get('mock')
    if mock_param is None:
        use_mock = USE_MOCK_DATA
    else:
        use_mock = mock_param.lower() in ('1', 'true', 'yes')

    weather_data = calculator.get_weather_data(city, force_mock=use_mock)
    recommendations = calculator.recommend_fruits(weather_data)
    return jsonify({
        'city': city,
        'weather': weather_data,
        'recommendations': recommendations
    })


@app.route('/api/geocode')
def api_geocode():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'lat and lon are required'}), 400

    key = API_KEYS.get('openweathermap')
    if not key or key == 'demo_key':
        # If no key, return coordinates directly
        return jsonify({'city': None, 'country': None, 'lat': lat, 'lon': lon})

    try:
        url = f'https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={key}'
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return jsonify({'error': 'reverse geocode failed', 'detail': r.text}), 500
        data = r.json()
        if not data:
            return jsonify({'city': None, 'country': None, 'lat': lat, 'lon': lon})
        return jsonify({'city': data[0].get('name'), 'country': data[0].get('country'), 'lat': lat, 'lon': lon})
    except Exception as e:
        logger.exception('Reverse geocode failed')
        return jsonify({'error': 'reverse geocode failed', 'detail': str(e)}), 500


@app.route('/api/debug')
def api_debug():
    # Return lightweight debug information about providers and keys
    open_present = bool(API_KEYS.get('openweathermap') and API_KEYS['openweathermap'] != 'demo_key')
    weatherapi_present = bool(API_KEYS.get('weatherapi') and API_KEYS['weatherapi'] != 'demo_key')
    return jsonify({
        'openweathermap_key_present': open_present,
        'weatherapi_key_present': weatherapi_present,
        'openweathermap_key_valid': OPENWEATHER_KEY_VALID,
        'weatherapi_key_valid': WEATHERAPI_KEY_VALID,
        'use_mock': USE_MOCK_DATA
    })


@app.route('/api/clear_cache', methods=['POST'])
def api_clear_cache():
    calculator.weather_data_cache.clear()
    return jsonify({'cleared': True})

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.json
    city = data.get('city', 'London')
    fruit = data.get('fruit', 'beetroot')
    panel_size = data.get('panel_size', 2)
    
    # Allow overriding use of mock/live per request via `mock` boolean
    body_mock = data.get('mock')
    if body_mock is None:
        use_mock = USE_MOCK_DATA
    else:
        use_mock = bool(body_mock)

    weather_data = calculator.get_weather_data(city, force_mock=use_mock)
    power_output = calculator.calculate_power_output(fruit, panel_size, weather_data)
    installation = calculator.calculate_installation_requirements(fruit, panel_size)
    
    return jsonify({
        'power_output': power_output,
        'installation': installation,
        'weather': weather_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

    