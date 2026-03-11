import aiohttp

URL = "https://carburanti.mise.gov.it/ospzApi/search/zone"

async def search_fuel_stations(lat: float, lon: float, radius: int = 10, fuel_type: str = "2-1"):
    """
    Cerca i benzinai tramite API MISE.
    fuel_type "2-1" corrisponde generalmente al Gasolio (Self).
    """
    payload = {
        "points": [
            {
                "lat": lat,
                "lng": lon
            }
        ],
        "fuelType": fuel_type,
        "priceOrder": "asc",
        "radius": radius
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            return None