import pydantic
import typing
import bcrypt
import json
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, Integer, String, DateTime, func, Text, ForeignKey


class CreateUser(pydantic.BaseModel):
    mail: str
    password: str


class PatchUser(pydantic.BaseModel):
    mail: typing.Optional[str]
    password: typing.Optional[str]


def validate(model, raw_data: dict):
    try:
        return model(**raw_data).dict()
    except pydantic.ValidationError as error:
        raise BadRequest(message='validate error')


app = web.Application()

PG_DSN = 'postgresql+asyncpg://aiohttps:12345@127.0.0.1:5432/aiohttps'

engine = create_async_engine(PG_DSN, echo=True)
Base = declarative_base()


class HttpError(web.HTTPError):
    def __init__(self, *, headers=None, reason=None, body=None, message=None):
        json_response = json.dumps({'error': message})
        super().__init__(
            headers=headers,
            reason=reason,
            body=body,
            text=json_response,
            content_type='application/json'
        )


class BadRequest(HttpError):
    status_code = 400


class NotFound(HttpError):
    status_code = 404


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    mail = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password.encode())


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


class Advertisement(Base):

    __tablename__ = 'advertisement'

    id = Column(Integer, primary_key=True)
    header = Column(String, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    owner = Column(Integer, ForeignKey('user.id'))


class UserView(web.View):

    async def get(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            return web.json_response(
                {
                    'id': user.id,
                    'mail': user.mail
                }
            )

    async def post(self):
        user_data = validate(CreateUser, await self.request.json())
        user_data['password'] = hash_password(user_data['password'])
        new_user = User(**user_data)
        async with app.async_session_maker() as session:
            try:
                session.add(new_user)
                await session.commit()
                return web.json_response({'id': new_user.id})
            except IntegrityError as er:
                raise BadRequest(message='user already exist')

    async def patch(self):
        user_id = int(self.request.match_info['user_id'])
        user_data = validate(PatchUser, await self.request.json())
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            for column, value in user_data.items():
                setattr(user, column, value)
            session.add(user)
            await session.commit()
            return web.json_response({'status': 'success'})

    async def delete(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            await session.delete(user)
            await session.commit()
            return web.json_response({'status': 'success'})


class AdvertisementView(web.View):

    async def get(self):
        adv_id = int(self.request.match_info['adv_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_adv(adv_id, session)
            return web.json_response({'id': advertisement.id, 'header': advertisement.header, 'created_at': str(advertisement.created_at)})

    async def post(self):
        adv_data = await self.request.json()
        adv_data['owner'] = int(adv_data['owner'])
        new_adv = Advertisement(**adv_data)

        async with app.async_session_maker() as session:
            try:
                session.add(new_adv)
                await session.commit()
                return web.json_response({'id': new_adv.id, 'header': new_adv.header, 'owner': new_adv.owner})
            except IntegrityError as er:
                raise BadRequest(message='advertisement already exist')

    async def patch(self):
        adv_id = int(self.request.match_info['adv_id'])
        adv_data = await self.request.json()
        adv_data['owner'] = int(adv_data['owner'])
        async with app.async_session_maker() as session:
            advertisement = await get_adv(adv_id, session)
            for column, value in adv_data.items():
                setattr(advertisement, column, value)
            session.add(advertisement)
            await session.commit()
            return web.json_response({'status': 'success'})

    async def delete(self):
        adv_id = int(self.request.match_info['adv_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_adv(adv_id, session)
            await session.delete(advertisement)
            await session.commit()
            return web.json_response({'status': 'success'})


async def get_user(user_id: int, session):
    user = await session.get(User, user_id)
    if user is None:
        raise NotFound(message='user not found')
    return user


async def get_adv(adv_id: int, session):
    advertisement = await session.get(Advertisement, adv_id)
    if advertisement is None:
        raise NotFound(message='advertisement not found')
    return advertisement


async def init_orm(app: web.Application):

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session_maker = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        app.async_session_maker = async_session_maker
        yield


app.cleanup_ctx.append(init_orm)

app.router.add_route('POST', '/users/', UserView)
app.router.add_route('GET', '/users/{user_id:\d+}', UserView)
app.router.add_route('PATCH', '/users/{user_id:\d+}', UserView)
app.router.add_route('DELETE', '/users/{user_id:\d+}', UserView)

app.router.add_route('POST', '/adv/', AdvertisementView)
app.router.add_route('GET', '/adv/{adv_id:\d+}', AdvertisementView)
app.router.add_route('PATCH', '/adv/{adv_id:\d+}', AdvertisementView)
app.router.add_route('DELETE', '/adv/{adv_id:\d+}', AdvertisementView)

web.run_app(app)
