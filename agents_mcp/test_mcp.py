import asyncio

from tools import get_flights


async def main():

    hotels = await get_flights()

    print(hotels)


asyncio.run(main())