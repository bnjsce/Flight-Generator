<<<<<<< HEAD
import math
from pyflightdata import FlightData
from datetime import datetime, timedelta

f = FlightData()

class Flight:
	def __init__(self, rand_flight, origin_iata):
		'''
		Initialise Flight object. All variables are public
		'''
		self.origin_details = f.get_airport_details(origin_iata)
		# identification
		self.callsign = rand_flight['identification']['callsign']
		self.aircraft_type = rand_flight['aircraft']['model']['text']
		# departure info
		self.departure_name = f"{self.origin_details['name']}, {self.origin_details['position']['region']['city']}, {self.origin_details['position']['country']['name']}"
		self.departure_icao = self.origin_details['code']['icao']
		self.departure_iata = self.origin_details['code']['iata']
		self.departure_terminal = rand_flight['airport']['origin']['info']['terminal']
		self.departure_gate = rand_flight['airport']['origin']['info']['gate']
		# arrival info
		self.arrival_name = f"{rand_flight['airport']['destination']['name']}, {rand_flight['airport']['destination']['position']['region']['city']}, {rand_flight['airport']['destination']['position']['country']['name']}"
		self.arrival_icao = rand_flight['airport']['destination']['code']['icao']
		self.arrival_iata = rand_flight['airport']['destination']['code']['iata']
		self.arrival_terminal = rand_flight['airport']['destination']['info']['terminal']
		self.arrival_gate = rand_flight['airport']['destination']['info']['gate']
		# METAR and distance data
		self.departure_coords = (self.origin_details['position']['latitude'], self.origin_details['position']['longitude'])
		self.arrival_coords = (rand_flight['airport']['destination']['position']['latitude'], rand_flight['airport']['destination']['position']['longitude'])
		self.departure_metar = f.get_airport_metars(self.departure_iata)
		self.arrival_metar = f.get_airport_metars(self.arrival_iata)
		self.distance = self.calc_distance(self.departure_coords, self.arrival_coords)
		self.block_time = self.calc_flight_time(rand_flight['time']['scheduled']['departure_time'], rand_flight['time']['scheduled']['arrival_time'])

	@staticmethod
	def calc_distance(coord1, coord2) -> int:
		'''
		Calculate the distance between two airports 'as the crow flies.'

		Parameters:
		coord1 (tuple): Lat and long of origin.
		coord2 (tuple): Lat and long of destination.

		Returns:
		(int): Distance in nautical miles to 2 d.p.
		'''
		R = 6371.0 # radius of Earth in km

		lat1, lon1 = map(math.radians, coord1) # must be in radians for Haversine calc
		lat2, lon2 = map(math.radians, coord2)

		dlat = lat2 - lat1 # delta
		dlon = lon2 - lon1

		a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
		c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

		return round(R * c * 0.539957, 2) # distance in nautical miles

	@staticmethod
	def calc_flight_time(departure, arrival) -> str:
		# parse times
		dep_time = datetime.strptime(departure, '%H%M')
		arr_time = datetime.strptime(arrival, '%H%M')

		# if arrival is earlier => next day
		if arr_time < dep_time:
			arr_time += timedelta(days=1)

		# calc difference
		duration = arr_time - dep_time

		hours, remainder = divmod(duration.seconds, 3600)
		minutes = remainder // 60

=======
import math
from pyflightdata import FlightData
from datetime import datetime, timedelta

f = FlightData()

class Flight:
	def __init__(self, rand_flight, origin_iata):
		'''
		Initialise Flight object. All variables are public
		'''
		self.origin_details = f.get_airport_details(origin_iata)
		# identification
		self.callsign = rand_flight['identification']['callsign']
		self.aircraft_type = rand_flight['aircraft']['model']['text']
		# departure info
		self.departure_name = f"{self.origin_details['name']}, {self.origin_details['position']['region']['city']}, {self.origin_details['position']['country']['name']}"
		self.departure_icao = self.origin_details['code']['icao']
		self.departure_iata = self.origin_details['code']['iata']
		self.departure_terminal = rand_flight['airport']['origin']['info']['terminal']
		self.departure_gate = rand_flight['airport']['origin']['info']['gate']
		# arrival info
		self.arrival_name = f"{rand_flight['airport']['destination']['name']}, {rand_flight['airport']['destination']['position']['region']['city']}, {rand_flight['airport']['destination']['position']['country']['name']}"
		self.arrival_icao = rand_flight['airport']['destination']['code']['icao']
		self.arrival_iata = rand_flight['airport']['destination']['code']['iata']
		self.arrival_terminal = rand_flight['airport']['destination']['info']['terminal']
		self.arrival_gate = rand_flight['airport']['destination']['info']['gate']
		# METAR and distance data
		self.departure_coords = (self.origin_details['position']['latitude'], self.origin_details['position']['longitude'])
		self.arrival_coords = (rand_flight['airport']['destination']['position']['latitude'], rand_flight['airport']['destination']['position']['longitude'])
		self.departure_metar = f.get_airport_metars(self.departure_iata)
		self.arrival_metar = f.get_airport_metars(self.arrival_iata)
		self.distance = self.calc_distance(self.departure_coords, self.arrival_coords)
		self.block_time = self.calc_flight_time(rand_flight['time']['scheduled']['departure_time'], rand_flight['time']['scheduled']['arrival_time'])

	@staticmethod
	def calc_distance(coord1, coord2) -> int:
		'''
		Calculate the distance between two airports 'as the crow flies.'

		Parameters:
		coord1 (tuple): Lat and long of origin.
		coord2 (tuple): Lat and long of destination.

		Returns:
		(int): Distance in nautical miles to 2 d.p.
		'''
		R = 6371.0 # radius of Earth in km

		lat1, lon1 = map(math.radians, coord1) # must be in radians for Haversine calc
		lat2, lon2 = map(math.radians, coord2)

		dlat = lat2 - lat1 # delta
		dlon = lon2 - lon1

		a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
		c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

		return round(R * c * 0.539957, 2) # distance in nautical miles

	@staticmethod
	def calc_flight_time(departure, arrival) -> str:
		# parse times
		dep_time = datetime.strptime(departure, '%H%M')
		arr_time = datetime.strptime(arrival, '%H%M')

		# if arrival is earlier => next day
		if arr_time < dep_time:
			arr_time += timedelta(days=1)

		# calc difference
		duration = arr_time - dep_time

		hours, remainder = divmod(duration.seconds, 3600)
		minutes = remainder // 60

>>>>>>> 238bca6 (v2.1.0 - Map update)
		return f'{hours}h {minutes}m'