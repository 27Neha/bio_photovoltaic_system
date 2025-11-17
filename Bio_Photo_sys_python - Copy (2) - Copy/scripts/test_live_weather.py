import requests

BASE = 'http://127.0.0.1:5000'

cities = ['London', 'Miami', 'Tokyo', 'New York']

for c in cities:
    r = requests.get(f"{BASE}/api/recommendations/{c}")
    if r.status_code == 200:
        data = r.json()
        print('\nCity:', data['city'])
        print('Weather:', data['weather'])
        print('Top fruits:')
        for f in data['recommendations']:
            print(' -', f['name'], f.get('suitability_score'))
    else:
        print('Failed to fetch', c, r.status_code, r.text)

print('\nDone')
