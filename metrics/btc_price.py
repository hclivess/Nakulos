import requests

def collect():
    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur,gbp')
        data = response.json()['bitcoin']
        return {
            'usd': data['usd'],
            'eur': data['eur'],
            'gbp': data['gbp']
        }
    except Exception as e:
        return {
            'usd': None,
            'eur': None,
            'gbp': None,
        }

if __name__ == "__main__":
    result = collect()
    print(result)