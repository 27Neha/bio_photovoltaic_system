# BioPhotovoltaic System

This project is a Flask-based demo that recommends fruits and calculates biophotovoltaic power output based on weather conditions. It supports both mock weather data and live weather APIs.

## Setup

1. Install dependencies

```powershell
pip install -r requirements.txt
```

2. Add API keys to `config.env` (create the file if it doesn't exist)

```dotenv
OPENWEATHER_API_KEY=your_openweather_api_key_here
WEATHERAPI_KEY=your_weatherapi_key_here
EXCHANGERATE_API_KEY=your_exchangerate_api_key_here
USE_MOCK_DATA=false
```

- `USE_MOCK_DATA=false` tells the app to use live weather providers (OpenWeatherMap or WeatherAPI). If the flag is `true` or unset, the app uses local mock data.
- The server returns up to 5 fruit recommendations by default; the number can be adjusted by the `top_n` argument to the recommendation API.
  
### How to get API keys
- OpenWeatherMap (free tier available): https://openweathermap.org/api. Sign up and create an API key. Use the Geocoding + OneCall endpoints for best results.
- WeatherAPI (free tier available): https://www.weatherapi.com/. Sign up and create an API key and use it if you prefer WeatherAPI.

Set the keys in `config.env`, then restart the app. Use the `Use Live Data` toggle in the SPA to switch between mock/live data per request; the UI will show the provider validation status.
You can verify provider key validity and runtime flags via the debug endpoint:
```powershell
curl "http://127.0.0.1:5000/api/debug"
```
Sample response shows whether keys are present and valid and if mock mode is in effect.

Developer tips:
- To force the SPA to use mock data, uncheck the "Use Live Data" toggle.
- To force an individual API request to use mock/live providers, append `?mock=true` or `?mock=false` to `/api/recommendations/<city>`.
- To force the JSON calculate call to use a provider, include `"mock": true/false` in the POST body.
- Use `/api/clear_cache` (POST) to clear cached weather results.

3. Run the app

```powershell
python app.py
```

4. Visit the app in a browser:

- Client SPA: http://127.0.0.1:5000/
- Server-rendered pages: http://127.0.0.1:5000/recommendations/City and http://127.0.0.1:5000/calculator?city=City

## Usage

- Click "Get Started" and enter a city or click "Use My Current Location" to automatically set your location and load recommendations.
- Ensure your `config.env` contains valid API keys and `USE_MOCK_DATA=false` to use live data.

## Notes & To-dos

- If you have concerns about security, avoid storing API keys in the repository. Consider using environment-specific secrets or a secret manager.
- Expand tests to cover API provider responses and caching.
- Improve UI error handling when API limits or failures occur.
