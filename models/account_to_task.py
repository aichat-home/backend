from sqlalchemy import ForeignKey, Table, Column

from db import Base


AccountToTask = Table(
    '_AccountToTask',
    Base.metadata,
    Column('A', ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True),
    Column('B', ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True)
)