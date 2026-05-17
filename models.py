import re
import datetime


class Flight:
    def __init__(self, index, departure_iata, departure_full,
                destination_iata, destination_full, price,
                airline, outbound_date, outbound_dep, outbound_arr,
                outbound_duration, outbound_stops, return_date,
                return_dep, return_arr, return_duration, return_stops):

        self.index = index
        self.departure_iata = departure_iata
        self.departure_full = departure_full
        self.destination_iata = destination_iata
        self.destination_full = destination_full
        self.price = price
        self.airline = airline
        self.outbound_date = outbound_date
        self.outbound_dep = outbound_dep
        self.outbound_arr = outbound_arr
        self.outbound_duration = outbound_duration
        self.outbound_stops = outbound_stops
        self.return_date = return_date
        self.return_dep = return_dep
        self.return_arr = return_arr
        self.return_duration = return_duration
        self.return_stops = return_stops

