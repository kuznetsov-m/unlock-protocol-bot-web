from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from datetime import datetime
from app import db

class TelegramUser(db.Model):
    __tablename__ = 'telegram_user'

    id = Column(db.Integer, primary_key=True)
    first_start_timestamp = Column(db.DateTime, index=True, default=datetime.utcnow)
    is_stopped = Column(db.Integer, default=0)
    first_name = Column(db.String)
    last_name = Column(db.String)
    account_address = Column(db.String)

    def __repr__(self):
        return (
            f'TelegramUser(id={self.id}, '
            f'first_name={self.first_name}, '
            f'last_name={self.last_name}, '
            f'account_address={self.account_address})'
        )