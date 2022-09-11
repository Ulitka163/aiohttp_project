import aiohttp
from asyncio import run


async def main():
    async with aiohttp.ClientSession(auth=None) as session:
        # response = await session.post('http://127.0.0.1:8080/users/', json={'mail': 'user_5', 'password': '123456'})
        # print(await response.json())
        # response = await session.get('http://127.0.0.1:8080/users/11')
        # print(await response.json())
        # response = await session.patch('http://127.0.0.1:8080/users/1', json={'mail': 'user_1_v2', 'password': '12345'})
        # print(await response.json())
        # response = await session.get('http://127.0.0.1:8080/users/2')
        # print(await response.json())
        # response = await session.delete('http://127.0.0.1:8080/users/2')
        # print(await response.json())
        # response = await session.get('http://127.0.0.1:8080/users/2')
        # print(await response.json())

        # response = await session.post('http://127.0.0.1:8080/adv/',
        #                               json={
        #                                   'header': 'adv_1',
        #                                   'description': 'disc_1',
        #                                   'owner': '11'
        #                               })
        # print(await response.json())
        # response = await session.get('http://127.0.0.1:8080/adv/2')
        # print(await response.json())
        # response = await session.patch('http://127.0.0.1:8080/adv/1',
        #                                json={
        #                                     'header': 'adv_1_v1',
        #                                     'description': 'disc_1_v1',
        #                                     'owner': '11'
        #                                })
        # print(await response.json())
        response = await session.get('http://127.0.0.1:8080/adv/1')
        print(await response.json())
        response = await session.delete('http://127.0.0.1:8080/adv/2')
        print(await response.json())


run(main())
