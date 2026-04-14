import asyncio, aiohttp

async def main():
    API_KEY = 'qCoXRSu6'
    API_SECRET = 'GhL6l32FUgm7tKgtRJVsngdF5Cp5j-JhVIr5Js4kvTQ'
    BASE = 'https://test.deribit.com/api/v2'
    async with aiohttp.ClientSession() as s:
        r = await s.get(f'{BASE}/public/auth', params={
            'grant_type': 'client_credentials',
            'client_id': API_KEY, 'client_secret': API_SECRET
        })
        token = (await r.json())['result']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        r2 = await s.get(f'{BASE}/private/buy', params={
            'instrument_name': 'BTC-PERPETUAL',
            'amount': 10,
            'type': 'market',
            'label': 'sentiment_test'
        }, headers=headers)
        result = await r2.json()
        if 'result' in result:
            order = result['result'].get('order', {})
            print(f'OK: id={order.get("order_id")} dir={order.get("direction")} amt={order.get("amount")}')
        else:
            print(f'FAIL: {result}')

asyncio.run(main())
