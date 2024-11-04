import time

from fastapi import Request

from sqlalchemy import inspect

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend

from db import database
from models import User, Account, Wallet, Farm, Partner, Task, Reward, RefferAccount, Add, Activity, DailyActivity, SolanaWallet, Swap, Withdraw
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
    column_list = ['id', 'icon', 'type', 'title', 'amount', 'link', 'chatId', 'rank', 'user_completed_count']
    column_details_list = ['id', 'icon', 'type', 'title', 'amount', 'link', 'chatId', 'rank']
    form_columns = ['icon', 'type', 'title', 'amount', 'link', 'chatId', 'rank']


class PartnerView(ModelView, model=Partner):
    column_list = ['id', 'name', 'inviteCode', 'users_count']
    column_details_list = ['id', 'name', 'inviteCode']
    form_columns = ['id', 'name', 'inviteCode']
    

def create_admin(app):
    authentication_backend = AdminAuth(secret_key=settings.telegram_token)
    admin = Admin(app=app, engine=database.engine, authentication_backend=authentication_backend)
    [admin.add_view(create_view(model)) for model in [User, Account, Wallet, Farm, Reward, RefferAccount, Add, Activity, DailyActivity, SolanaWallet, Swap, Withdraw]]
    admin.add_view(TaskView)
    admin.add_view(PartnerView)

    return admin