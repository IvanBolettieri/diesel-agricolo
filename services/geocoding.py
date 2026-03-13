import aiohttp

async def search_location(query: str):
    """Cerca una località su OpenStreetMap (Nominatim)"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 10,
        'addressdetails': 1,
        'countrycodes': 'it' # Limitiamo la ricerca all'Italia
    }
    headers = {'User-Agent': 'FuelBot/1.0'}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            return []