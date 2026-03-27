from sqlalchemy import create_engine, Column, Integer, String, JSON, Text, exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import json

SQLALCHEMY_DATABASE_URL = "sqlite:///./nursery.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    meta = Column(JSON, nullable=False, default=dict)

class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)

class IRDevices(Base):
    __tablename__ = "ir_devices"
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True)
    frequency = Column(Integer, nullable=False)
    signal = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def __serialize(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def __deserialize(value, default):
    if value is None:
        return default

    if isinstance(default, bool):
        return value.lower() in ("true", "1", "yes")

    if isinstance(default, int):
        return int(value)

    if isinstance(default, float):
        return float(value)

    if isinstance(default, (dict, list)):
        return json.loads(value)

    return value

def get_profile() -> dict:
    db = next(get_db())
    user = db.query(User).first()
    if user:
        return { "id": user.id, "name": user.username, "email": user.email or "", "meta": user.meta }
    
    return {}

def get_settings(defaults: dict) -> dict:
    db = next(get_db())
    result = {}

    existing = {
        s.key: s for s in db.query(Settings).filter(Settings.key.in_(defaults.keys())).all()
    }

    for key, default_value in defaults.items():
        if key not in existing:
            db.add(Settings(key=key, value=__serialize(default_value)))
            result[key] = default_value
        else:
            result[key] = __deserialize(existing[key].value, default_value)

    db.commit()
    return result

def save_settings(settings: dict):
    db = next(get_db())

    for key, value in settings.items():
        existing = db.query(Settings).filter(Settings.key == key).first()

        if existing:
            existing.value = __serialize(value)
        else:
            db.add(Settings(key=key, value=__serialize(value)))

    db.commit()

def save_ir_device(tag, signal, frequency=38000):
    db = next(get_db())
    if db.query(exists().where(IRDevices.tag == tag)).scalar():
        return False

    db.add(IRDevices(tag=tag, frequency=frequency, signal=signal))
    db.commit()

    return True

def get_ir_device(id):
    db = next(get_db())
    device = db.query(IRDevices).filter_by(id=id).first()
    if device:
        return {
            "tag": device.tag,
            "frequency": device.frequency,
            "signal": device.signal
        }
    
    return None

def remove_ir_device(id):
    db = next(get_db())
    return db.query(IRDevices).filter_by(id=id).delete() > 0

def get_ir_devices():
    result = []

    db = next(get_db())
    devices = db.query(IRDevices).all()
    for device in devices:
        result.append({
            "id": device.id,
            "tag": device.tag,
            "frequency": device.frequency
        })
    
    return result

def check_new_install(db: Session):
    return db.query(User).count() == 0