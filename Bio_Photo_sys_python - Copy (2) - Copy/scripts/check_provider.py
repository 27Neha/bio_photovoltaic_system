import requests

for city in ['London','Jalgaon','Miami','Mulshi','Tokyo','New York','Los Angeles','Sydney']:
    url = f'http://127.0.0.1:5000/api/recommendations/{city}?mock=false'
    r = requests.get(url)
    print(city, r.status_code)
    if r.ok:
        j = r.json()
        print('provider:', j.get('weather', {}).get('provider'))
        print('weather keys:', list(j.get('weather', {}).keys()))
    else:
        print('Failed', r.text)
    print('-'*40)
