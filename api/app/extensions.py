from apscheduler.schedulers.background import BackgroundScheduler
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
# Not started in milestone 1. create_app() only configures the timezone.
scheduler = BackgroundScheduler()
