import aiohttp

from bot.config.settings import API_BASE_URL


async def _response_data(response: aiohttp.ClientResponse) -> dict:
    try:
        return await response.json()
    except aiohttp.ContentTypeError:
        return {
            "error": await response.text()
        }


async def get_services() -> list[dict]:
    url = f"{API_BASE_URL}/services/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return []

                return await response.json()
    except aiohttp.ClientError:
        return []


async def get_slots(date: str, service_id: int) -> list[dict]:
    url = f"{API_BASE_URL}/slots/"
    params = {
        "date": date,
        "service_id": service_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return []

                return await response.json()
    except aiohttp.ClientError:
        return []


async def create_booking(data: dict) -> tuple[bool, dict]:
    url = f"{API_BASE_URL}/bookings/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                response_data = await _response_data(response)

                if response.status == 201:
                    return True, response_data

                return False, response_data
    except aiohttp.ClientError:
        return False, {
            "error": "Не удалось подключиться к серверу."
        }


async def get_my_booking(telegram_id: int) -> dict | None:
    url = f"{API_BASE_URL}/my-booking/"
    params = {
        "telegram_id": telegram_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()

                return None
    except aiohttp.ClientError:
        return None


async def delete_booking(booking_id: int) -> bool:
    url = f"{API_BASE_URL}/bookings/{booking_id}/"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return response.status in [200, 204]
    except aiohttp.ClientError:
        return False


async def get_client_by_telegram_id(telegram_id: int) -> dict | None:
    url = f"{API_BASE_URL}/clients/by-telegram/"
    params = {
        "telegram_id": telegram_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()

                return None
    except aiohttp.ClientError:
        return None
