import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, Float, String, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from abc import ABC
import re
from datetime import datetime

load_dotenv()

DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def parse_price(price_str):
    return float(re.sub(r"[^\d.]", "", price_str))
    
def parse_duration(duration_str):
    duration_str = duration_str.strip().lower()
    
    if not duration_str or duration_str == "n/a":
        return 0
        
    hours = 0
    minutes = 0
    
    hours_match = re.search(r"(\d+)\s*h", duration_str)
    minutes_match = re.search(r"(\d+)\s*m", duration_str)
    
    if hours_match:
        hours = int(hours_match.group(1))
    if minutes_match:
        minutes = int(minutes_match.group(1))
    #fallbback    
    if hours == 0 and minutes == 0:
        digits = re.findall(r"\d+", duration_str)
        
        if len(digits) == 2:    
            hours = int(digits[0])
            minutes = int(digits[1])
        elif len(digits) == 1:  # e.g., 45 = 45m or 2 = 2h
            val = int(digits[0])
            if val > 12:
                minutes = val
            else:
                hours = val

    return (hours * 60) + minutes

def parse_stops(stops_input) -> int:
    stops_str = str(stops_input).strip().lower()
    
    if any(x in stops_str for x in ["direct", "n/a", "nonstop", ""]):
        return 0
        
    try:
        return int(stops_str)
    except ValueError:
        match = re.search(r'\d+', stops_str)
        if match:
            return int(match.group())
        return 0

class FlightModel(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)
    departure_iata = Column(String(3))
    departure_full = Column(String(100))
    destination_iata = Column(String(3))
    destination_full = Column(String(100))
    price = Column(Float)
    airline = Column(String(100))
    outbound_date = Column(String(50))
    outbound_dep = Column(String(10))
    outbound_arr = Column(String(10))
    outbound_duration = Column(Integer)
    outbound_stops = Column(Integer)
    return_date = Column(String(50))
    return_dep = Column(String(10))
    return_arr = Column(String(10))
    return_duration = Column(Integer)
    return_stops = Column(Integer)
    scraped_at = Column(TIMESTAMP, server_default=func.now())


    @classmethod
    def from_dict(cls, f):
        return cls(
            departure_iata   = f["departure_iata"],
            departure_full   = f["departure_full"],
            destination_iata = f["destination_iata"],
            destination_full = f["destination_full"],
            price            = parse_price(f["price"]),
            airline          = f["airline"],
            outbound_date    = f["outbound_date"],
            outbound_dep     = f["outbound_dep"],
            outbound_arr     = f["outbound_arr"],
            outbound_duration= parse_duration(f["outbound_duration"]),
            outbound_stops   = parse_stops(f["outbound_stops"]),
            return_date      = f["return_date"],
            return_dep       = f["return_dep"],
            return_arr       = f["return_arr"],
            return_duration  = parse_duration(f["return_duration"]),
            return_stops     = parse_stops(f["return_stops"]),
            scraped_at       = datetime.now()
        )
    
    
