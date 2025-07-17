from sqlalchemy import Column, Integer, Float, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class Viaje(Base):
    __tablename__ = 'viajes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inicio = Column(DateTime, default=datetime.datetime.utcnow)
    fin = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True)
    producto = Column(String, nullable=True)
    limite_min = Column(Float, nullable=True)
    limite_max = Column(Float, nullable=True)

    temperaturas = relationship("Temperatura", back_populates="viaje", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="viaje", cascade="all, delete-orphan")


class Temperatura(Base):
    __tablename__ = 'temperaturas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    viaje_id = Column(Integer, ForeignKey("viajes.id"), nullable=True)

    viaje = relationship("Viaje", back_populates="temperaturas")


class Alerta(Base):
    __tablename__ = 'alertas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mensaje = Column(String, nullable=False)
    color = Column(String, nullable=True)  # Ej: "rojo", "celeste"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    viaje_id = Column(Integer, ForeignKey("viajes.id"), nullable=True)
    viaje = relationship("Viaje", back_populates="alertas")

