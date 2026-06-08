from flight_db_interactions import FlightDBInteractions
import pandas as pd

    

class FlightSearch:
    def __init__(self):
        self.db = FlightDBInteractions()
    
    def get_flights(self, airport):
        return self.db.get_data(airport) 
    
    def sort_by_price(self, flights):
        return sorted(flights, key=lambda f: f.price)
    
    def cheapest_flights(self, flights, n=10):
        return flights[:n]
    
    def filter_direct(self, flights):
        return [f for f in flights if f.outbound_stops == 0]
