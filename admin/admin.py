import time

from fastapi import Request

from sqlalchemy import inspect

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from db import database
from models import User, Account, Wallet, Farm, Partner, Task, Reward, RefferAccount, Add
from core import settings


class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get('username')
        password = form.get('password')
        
        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({'token': username})
            request.session.update({'expires_at': time.time() + 86400})  # 1 hour expiry
            return True
        else:
            return False


    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True


    async def authenticate(self, request: Request) -> bool:
        token = request.session.get('token')
        expires_at = request.session.get('expires_at')

        if token is None or expires_at is None:
            return False
        
        if time.time() > expires_at:
            await self.logout(request)
            return False
        
        return True


def create_view(model):
    class View(ModelView, model=model):
        column_list = [column.name for column in model.__table__.columns]
        form_include_pk = True
        column_searchable_list = [column.name for column in model.__table__.columns]
        column_sortable_list = [column.name for column in model.__table__.columns]

        relationships = inspect(model).relationships
        column_list += [relation.key for relation in relationships]
    return View


class TaskView(ModelView, model=Task):
    column_list = [column.name for column in Task.__table__.columns]
    relationships = inspect(Task).relationships
    column_list += [relation.key for relation in relationships]

    column_formatters = {
        'userscompl': lambda m, a: len(m.usersCompleted)  # Count of completed users
    }


def create_admin(app):
    authentication_backend = AdminAuth(secret_key=settings.telegram_token)
    admin = Admin(app=app, engine=database.engine, authentication_backend=authentication_backend)
    [admin.add_view(create_view(model)) for model in [User, Account, Wallet, Farm, Partner, Reward, RefferAccount, Add]]
    admin.add_view(TaskView)

    return admin