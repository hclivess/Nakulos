import requests


def collect():
    metrics = {}

    try:
        response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur,gbp')
        data = response.json()['bitcoin']

        metrics['bitcoin_price_usd'] = {
            'value': data['usd']
        }
        metrics['bitcoin_price_eur'] = {
            'value': data['eur']
        }
        metrics['bitcoin_price_gbp'] = {
            'value': data['gbp']
        }
    except Exception as e:
        metrics['bitcoin_price_usd'] = {
            'value': None,
            'message': f"UnexpectedError: {str(e)}"
        }
        metrics['bitcoin_price_eur'] = {
            'value': None,
            'message': f"UnexpectedError: {str(e)}"
        }
        metrics['bitcoin_price_gbp'] = {
            'value': None,
            'message': f"UnexpectedError: {str(e)}"
        }

    return metrics


if __name__ == "__main__":
    result = collect()
    print(result)