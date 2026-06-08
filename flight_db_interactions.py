import json
import os
import asyncio
from datetime import datetime
from models import Flight
from scraper import Scraper
from database import Session, FlightModel, parse_price, parse_duration, parse_stops

class FlightDBInteractions:
    
    def is_stale(self, airport):
        with Session() as session:
            result = session.query(FlightModel)\
                .filter(FlightModel.departure_iata == airport.upper())\
                .order_by(FlightModel.scraped_at.desc())\
                .first()
        if not result:
            return True
        age = datetime.now() - result.scraped_at
        return age.total_seconds() > 172800
    
    def read(self, airport, order_by="price"):
        session = Session()
        rows = session.query(FlightModel)\
            .filter(FlightModel.departure_iata == airport.upper())\
            .order_by(FlightModel.price)\
            .all()
        session.close()
        
        return [Flight(
            index=row.id,
            departure_iata = row.departure_iata,
            departure_full = row.departure_full,
            destination_iata = row.destination_iata,
            destination_full = row.destination_full,
            price = row.price,
            airline = row.airline,
            outbound_date = row.outbound_date,
            outbound_dep = row.outbound_dep,
            outbound_arr = row.outbound_arr,
            outbound_duration = row.outbound_duration,
            outbound_stops = row.outbound_stops,
            return_date = row.return_date,
            return_dep = row.return_dep,
            return_arr = row.return_arr,
            return_duration = row.return_duration,
            return_stops = row.return_stops,
        ) for row in rows]
        
    def write(self, flights, airport):
        from database import Session, FlightModel #local to avoid circular
        session = Session()
        try:
            session.query(FlightModel).filter(FlightModel.departure_iata == airport.upper()).delete()
            
            models_to_add = [FlightModel.from_dict(f) for f in flights]
                
            session.add_all(models_to_add)
            session.commit()
            print(f"DB WRITE SUCCESS: Committed {len(models_to_add)} flights for {airport}")
        except Exception as e:
            session.rollback()
            print(f"DB WRITE ERROR: Failed to save flights to DB: {e}")
        finally:
            session.close()  

    def get_data(self, airport):
        if not airport:
            print("WARNING: get_data called with an empty airport string.")
            return []

        if self.is_stale(airport):
            print(f"Data for {airport} is stale/missing. Launching scraper...")
            scraper = Scraper(headless=False) #debug change to true once confirmed working
            asyncio.run(scraper.run(airport))
            
            json_path = "kiwi_flights.json"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    scraped_data = json.load(f)
                
                self.write(scraped_data, airport)
            else:
                print("WARNING: Scraper finished but kiwi_flights.json was not found.")
                
        return self.read(airport=airport)