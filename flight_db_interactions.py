import json
import os
from datetime import datetime
from models import Flight
from scraper import Scraper
from database import Session, FlightModel



class FlightDBInteractions:
    
    
    def is_stale(self, airport):
        with Session() as session:
            result = session.query(FlightModel)\
                .filter(FlightModel.departure_iata == airport)\
                .order_by(FlightModel.scraped_at.desc())\
                .first()
        if not result:
            return True
        age = datetime.now() - result.scraped_at
        return age.total_seconds() > 172800
    
    def read(self, order_by="price", airport="ABZ"):
        session = Session()
        rows = session.query(FlightModel)\
            .filter(FlightModel.departure_iata == airport)\
            .order_by(FlightModel.price)\
            .all()
        session.close()
        return [Flight(
            index=row.id,
            departure_iata = row.departure_iata,
            departure_full = row.departure_full,
            destination_iata = row.destination_iata,
            destination_full = row.destination_full,
            price = float(row.price),
            airline = row.airline,
            outbound_date = row.outbound_date,
            outbound_dep = row.outbound_dep,
            outbound_arr = row.outbound_arr,
            outbound_duration = int(row.outbound_duration),
            outbound_stops = int(row.outbound_stops),
            return_date = row.return_date,
            return_dep = row.return_dep,
            return_arr = row.return_arr,
            return_duration = int(row.return_duration),
            return_stops = int(row.return_stops),
            ) for row in rows]
        
    
    def write(self, flights):
        session = Session()
        session.query(FlightModel).delete()
        session.add_all([FlightModel.from_dict(f) for f in flights])
        session.commit()
        session.close()        


    def get_data(self, airport="ABZ"):
        if self.is_stale(airport):
            import asyncio
            from scraper import Scraper
            scraper = Scraper()
            asyncio.run(scraper.run(airport))
        return self.read(airport)


