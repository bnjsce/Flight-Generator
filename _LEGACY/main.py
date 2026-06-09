<<<<<<< HEAD
import math
import random
import secrets
import sys, os
from pyflightdata import FlightData
from datetime import datetime, timedelta

f = FlightData()

def clear() -> None:
	'''
	Clears the screen.
	'''
	os.system('cls' if os.name=='nt' else 'clear')

def line_br() -> None:
	'''
	Print a line break with dashes.
	'''
	print('-------------------------------------------------------------------')

def write_data(data) -> None:
	'''
	Write config data to config file.

	Parameters:
	data (list): List containing airport(s), airline(s), and plane(s).
	'''
	with open('./config.txt', 'w') as f:
		# write departure airports
		for i in range(len(data[0])):
			if i == len(data[0]) - 1:
				f.write(data[0][i] + '\n')
			else:
				f.write(data[0][i] + ',')

		# write airlines
		for j in range(len(data[1])):
			if j == len(data[1]) - 1:
				f.write(data[1][j] + '\n')
			else:
				f.write(data[1][j] + ',')

		# write aircraft models
		for k in range(len(data[2])):
			if k == len(data[2]) - 1:
				f.write(data[2][k] + '\n')
			else:
				f.write(data[2][k] + ',')

		f.write(data[3])

def get_user_config() -> list:
	'''
	Retrieve user config file for search filter. Prompt user to set it up if path doesn't exist or file is empty.

	Returns:
	temp (list): [[AIRPORT1, AIRPORT2, ETC], [AIRLINE1, AIRLINE2, ETC], [PLANE1, PLANE2, ETC]]
	'''
	if not os.path.exists('./config.txt'):
		print('No config file detected, please set it up:')
		airports = []
		airlines = []
		planes = []

		# departure airports
		print('Which departure airport(s)? Type !stop to exit and save.')
		airport_in = None
		while airport_in != '!stop':
			airport_in = input('IATA: ').replace(' ', '').replace(',', '')
			if airport_in != '!stop':
				airports.append(airport_in.upper())

		# airlines
		print('Which airline(s)? Type !stop to exit and save.')
		airline_in = None
		while airline_in != '!stop':
			airline_in = input('Callsign prefix: ').replace(' ', '').replace(',', '')
			if airline_in != '!stop':
				airlines.append(airline_in.upper())

		# aircraft models
		print('Which aircraft model(s)? Type !stop to exit and save.')
		plane_in = None
		while plane_in != '!stop':
			plane_in = input('Aircraft: ').replace(' ', '').replace(',', '')
			if plane_in != '!stop':
				planes.append(plane_in.upper())

		max_time = input('Maximum block time (hours): ').lower().replace(' ', '').replace(',', '')

		temp = [airports, airlines, planes, max_time]
		write_data(temp)
		clear()
		return temp
	else:
		data = None
		with open('./config.txt', 'r') as f:
			data = f.readlines()

		if len(data) < 4:
			print('Invalid config file detected, please set it up:')
			airports = []
			airlines = []
			planes = []

			# departure airports
			print('Which departure airport(s)? Type !stop to exit and save.')
			airport_in = None
			while airport_in != '!stop':
				airport_in = input('IATA: ').replace(' ', '').replace(',', '')
				if airport_in != '!stop':
					airports.append(airport_in.upper())

			# airlines
			print('Which airline(s)? Type !stop to exit and save.')
			airline_in = None
			while airline_in != '!stop':
				airline_in = input('Callsign prefix: ').replace(' ', '').replace(',', '')
				if airline_in != '!stop':
					airlines.append(airline_in.upper())

			# aircraft models
			print('Which aircraft model(s)? Type !stop to exit and save.')
			plane_in = None
			while plane_in != '!stop':
				plane_in = input('Aircraft: ').replace(' ', '').replace(',', '')
				if plane_in != '!stop':
					planes.append(plane_in.upper())

			max_time = input('Maximum block time (hours): ').lower().replace(' ', '').replace(',', '')

			temp = [airports, airlines, planes, max_time]
			write_data(temp)
			clear()
			return temp
		else:
			airports = data[0].replace('\n', '').split(',')
			airlines = data[1].replace('\n', '').split(',')
			planes = data[2].replace('\n', '').split(',')
			max_time = int(data[3])
			temp = [airports, airlines, planes, max_time]
			return temp

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

	return f'{hours}h {minutes}m'

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

def flight_details(rand_flight, origin_iata) -> None:
	'''
	Displays the essential details of the flight, as well as a METAR report.

	Parameters:
	rand_flight (dict): Randomly-selected flight.
	origin_iata (str): IATA code of the departure airport.
	'''
	line_br()
	print('IDENTIFICATION')
	line_br()
	print(f"Flight number: {rand_flight['identification']['callsign']}") # callsign
	print(f"Aircraft: {rand_flight['aircraft']['model']['text']}") # aircraft type
	line_br()
	print('DEPARTURE INFO')
	line_br()
	origin_details = f.get_airport_details(origin_iata)
	print(f"Departure: {origin_details['name']}, {origin_details['position']['region']['city']}, {origin_details['position']['country']['name']}")
	print(f"ICAO/IATA: {origin_details['code']['icao']}/{origin_details['code']['iata']}")
	print(f"Terminal: {rand_flight['airport']['origin']['info']['terminal']}")
	print(f"Gate: {rand_flight['airport']['origin']['info']['gate']}")
	line_br()
	print('ARRIVAL INFO')
	line_br()
	dest = rand_flight['airport']['destination']
	print(f"Arrival: {dest['name']}, {dest['position']['region']['city']}, {dest['position']['country']['name']}") # airport name, city, and country
	print(f"ICAO/IATA: {dest['code']['icao']}/{dest['code']['iata']}") # airport ICAO
	print(f"Terminal: {dest['info']['terminal']}")
	print(f"Gate: {dest['info']['gate']}")

	# METAR and distance data
	dest_coords = (dest['position']['latitude'], dest['position']['longitude']) # lat and lon of airport
	dest_icao = dest['code']['icao']
	origin_metar = f.get_airport_metars(origin_iata)
	origin_coords = (origin_details['position']['latitude'], origin_details['position']['longitude'])
	line_br()
	print('FLIGHT INFO')
	line_br()
	print(f'Distance: {calc_distance(origin_coords, dest_coords)} NM')
	print(f"Est. Block time: {calc_flight_time(rand_flight['time']['scheduled']['departure_time'], rand_flight['time']['scheduled']['arrival_time'])}")
	line_br()
	print('METAR REPORT')
	line_br()
	try:
		print(f'{origin_metar}\n')
		print(f.get_airport_metars(dest_icao) + '\n') # destination METAR report
	except:
		print('There was an error loading the METAR report.')
	input('Press enter to close...')
	exit()

def main() -> None:
	'''
	Randomly selects a flight based on user config data.
	'''
	clear()
	user_config = get_user_config()

	suitable_flights = []

	change_config = input('Would you like to change your config? (y/n) >>> ').replace(' ', '').lower()
	if change_config == 'y' or change_config == 'yes':
		with open('./config.txt', 'w') as file:
			file.write('')
		main()
	else:
		clear()
		print(f'CONFIG: {user_config}\n')
		temp = []
		for i in range(len(user_config[0])):
			origin_iata = user_config[0][i]
			origin_departures = f.get_airport_departures(origin_iata, limit=25, earlier_data=True)
			flight_count = 0
			for departure in origin_departures:
				accepted_airlines = user_config[1]
				accepted_aircraft = user_config[2]
				flight = departure['flight']

				if any(flight['identification']['callsign'].startswith(prefix) for prefix in accepted_airlines) and flight['aircraft']['model']['code'] in accepted_aircraft:
					block_time = calc_flight_time(flight['time']['scheduled']['departure_time'], flight['time']['scheduled']['arrival_time']).split(' ')
					block_time_h = int(block_time[0].replace('h', ''))
					block_time_m = int(block_time[1].replace('m', ''))
					if block_time_h < int(user_config[3]) or (block_time_h == int(user_config[3]) and block_time_m == 0):
						suitable_flights.append(flight)
						flight_count += 1
			temp.append(f'{origin_iata}{flight_count}')

		rand_flight = None
		if len(suitable_flights) == 0:
			print('Currently no available flights. Please try again in a few minutes or check your config file.') # if no flights returned
			input('Press enter to close...')
			exit()
		else:
			random.seed(secrets.randbits(64))
			rand_idx = random.randint(0, len(suitable_flights) - 1)
			tracking = 1
			selected_iata = 0
			while tracking < rand_idx:
				airport_flights = int(temp[selected_iata][3:])
				
				if tracking + airport_flights < rand_idx:
					tracking += airport_flights
					selected_iata += 1
				elif tracking + airport_flights > rand_idx or tracking + airport_flights == rand_idx:
					tracking = rand_idx

			rand_flight = suitable_flights[rand_idx]
			flight_details(rand_flight, temp[selected_iata][:3])

# run main
if __name__ == '__main__':
=======
import math
import random
import secrets
import sys, os
from pyflightdata import FlightData
from datetime import datetime, timedelta

f = FlightData()

def clear() -> None:
	'''
	Clears the screen.
	'''
	os.system('cls' if os.name=='nt' else 'clear')

def line_br() -> None:
	'''
	Print a line break with dashes.
	'''
	print('-------------------------------------------------------------------')

def write_data(data) -> None:
	'''
	Write config data to config file.

	Parameters:
	data (list): List containing airport(s), airline(s), and plane(s).
	'''
	with open('./config.txt', 'w') as f:
		# write departure airports
		for i in range(len(data[0])):
			if i == len(data[0]) - 1:
				f.write(data[0][i] + '\n')
			else:
				f.write(data[0][i] + ',')

		# write airlines
		for j in range(len(data[1])):
			if j == len(data[1]) - 1:
				f.write(data[1][j] + '\n')
			else:
				f.write(data[1][j] + ',')

		# write aircraft models
		for k in range(len(data[2])):
			if k == len(data[2]) - 1:
				f.write(data[2][k] + '\n')
			else:
				f.write(data[2][k] + ',')

		f.write(data[3])

def get_user_config() -> list:
	'''
	Retrieve user config file for search filter. Prompt user to set it up if path doesn't exist or file is empty.

	Returns:
	temp (list): [[AIRPORT1, AIRPORT2, ETC], [AIRLINE1, AIRLINE2, ETC], [PLANE1, PLANE2, ETC]]
	'''
	if not os.path.exists('./config.txt'):
		print('No config file detected, please set it up:')
		airports = []
		airlines = []
		planes = []

		# departure airports
		print('Which departure airport(s)? Type !stop to exit and save.')
		airport_in = None
		while airport_in != '!stop':
			airport_in = input('IATA: ').replace(' ', '').replace(',', '')
			if airport_in != '!stop':
				airports.append(airport_in.upper())

		# airlines
		print('Which airline(s)? Type !stop to exit and save.')
		airline_in = None
		while airline_in != '!stop':
			airline_in = input('Callsign prefix: ').replace(' ', '').replace(',', '')
			if airline_in != '!stop':
				airlines.append(airline_in.upper())

		# aircraft models
		print('Which aircraft model(s)? Type !stop to exit and save.')
		plane_in = None
		while plane_in != '!stop':
			plane_in = input('Aircraft: ').replace(' ', '').replace(',', '')
			if plane_in != '!stop':
				planes.append(plane_in.upper())

		max_time = input('Maximum block time (hours): ').lower().replace(' ', '').replace(',', '')

		temp = [airports, airlines, planes, max_time]
		write_data(temp)
		clear()
		return temp
	else:
		data = None
		with open('./config.txt', 'r') as f:
			data = f.readlines()

		if len(data) < 4:
			print('Invalid config file detected, please set it up:')
			airports = []
			airlines = []
			planes = []

			# departure airports
			print('Which departure airport(s)? Type !stop to exit and save.')
			airport_in = None
			while airport_in != '!stop':
				airport_in = input('IATA: ').replace(' ', '').replace(',', '')
				if airport_in != '!stop':
					airports.append(airport_in.upper())

			# airlines
			print('Which airline(s)? Type !stop to exit and save.')
			airline_in = None
			while airline_in != '!stop':
				airline_in = input('Callsign prefix: ').replace(' ', '').replace(',', '')
				if airline_in != '!stop':
					airlines.append(airline_in.upper())

			# aircraft models
			print('Which aircraft model(s)? Type !stop to exit and save.')
			plane_in = None
			while plane_in != '!stop':
				plane_in = input('Aircraft: ').replace(' ', '').replace(',', '')
				if plane_in != '!stop':
					planes.append(plane_in.upper())

			max_time = input('Maximum block time (hours): ').lower().replace(' ', '').replace(',', '')

			temp = [airports, airlines, planes, max_time]
			write_data(temp)
			clear()
			return temp
		else:
			airports = data[0].replace('\n', '').split(',')
			airlines = data[1].replace('\n', '').split(',')
			planes = data[2].replace('\n', '').split(',')
			max_time = int(data[3])
			temp = [airports, airlines, planes, max_time]
			return temp

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

	return f'{hours}h {minutes}m'

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

def flight_details(rand_flight, origin_iata) -> None:
	'''
	Displays the essential details of the flight, as well as a METAR report.

	Parameters:
	rand_flight (dict): Randomly-selected flight.
	origin_iata (str): IATA code of the departure airport.
	'''
	line_br()
	print('IDENTIFICATION')
	line_br()
	print(f"Flight number: {rand_flight['identification']['callsign']}") # callsign
	print(f"Aircraft: {rand_flight['aircraft']['model']['text']}") # aircraft type
	line_br()
	print('DEPARTURE INFO')
	line_br()
	origin_details = f.get_airport_details(origin_iata)
	print(f"Departure: {origin_details['name']}, {origin_details['position']['region']['city']}, {origin_details['position']['country']['name']}")
	print(f"ICAO/IATA: {origin_details['code']['icao']}/{origin_details['code']['iata']}")
	print(f"Terminal: {rand_flight['airport']['origin']['info']['terminal']}")
	print(f"Gate: {rand_flight['airport']['origin']['info']['gate']}")
	line_br()
	print('ARRIVAL INFO')
	line_br()
	dest = rand_flight['airport']['destination']
	print(f"Arrival: {dest['name']}, {dest['position']['region']['city']}, {dest['position']['country']['name']}") # airport name, city, and country
	print(f"ICAO/IATA: {dest['code']['icao']}/{dest['code']['iata']}") # airport ICAO
	print(f"Terminal: {dest['info']['terminal']}")
	print(f"Gate: {dest['info']['gate']}")

	# METAR and distance data
	dest_coords = (dest['position']['latitude'], dest['position']['longitude']) # lat and lon of airport
	dest_icao = dest['code']['icao']
	origin_metar = f.get_airport_metars(origin_iata)
	origin_coords = (origin_details['position']['latitude'], origin_details['position']['longitude'])
	line_br()
	print('FLIGHT INFO')
	line_br()
	print(f'Distance: {calc_distance(origin_coords, dest_coords)} NM')
	print(f"Est. Block time: {calc_flight_time(rand_flight['time']['scheduled']['departure_time'], rand_flight['time']['scheduled']['arrival_time'])}")
	line_br()
	print('METAR REPORT')
	line_br()
	try:
		print(f'{origin_metar}\n')
		print(f.get_airport_metars(dest_icao) + '\n') # destination METAR report
	except:
		print('There was an error loading the METAR report.')
	input('Press enter to close...')
	exit()

def main() -> None:
	'''
	Randomly selects a flight based on user config data.
	'''
	clear()
	user_config = get_user_config()

	suitable_flights = []

	change_config = input('Would you like to change your config? (y/n) >>> ').replace(' ', '').lower()
	if change_config == 'y' or change_config == 'yes':
		with open('./config.txt', 'w') as file:
			file.write('')
		main()
	else:
		clear()
		print(f'CONFIG: {user_config}\n')
		temp = []
		for i in range(len(user_config[0])):
			origin_iata = user_config[0][i]
			origin_departures = f.get_airport_departures(origin_iata, limit=25, earlier_data=True)
			flight_count = 0
			for departure in origin_departures:
				accepted_airlines = user_config[1]
				accepted_aircraft = user_config[2]
				flight = departure['flight']

				if any(flight['identification']['callsign'].startswith(prefix) for prefix in accepted_airlines) and flight['aircraft']['model']['code'] in accepted_aircraft:
					block_time = calc_flight_time(flight['time']['scheduled']['departure_time'], flight['time']['scheduled']['arrival_time']).split(' ')
					block_time_h = int(block_time[0].replace('h', ''))
					block_time_m = int(block_time[1].replace('m', ''))
					if block_time_h < int(user_config[3]) or (block_time_h == int(user_config[3]) and block_time_m == 0):
						suitable_flights.append(flight)
						flight_count += 1
			temp.append(f'{origin_iata}{flight_count}')

		rand_flight = None
		if len(suitable_flights) == 0:
			print('Currently no available flights. Please try again in a few minutes or check your config file.') # if no flights returned
			input('Press enter to close...')
			exit()
		else:
			random.seed(secrets.randbits(64))
			rand_idx = random.randint(0, len(suitable_flights) - 1)
			tracking = 1
			selected_iata = 0
			while tracking < rand_idx:
				airport_flights = int(temp[selected_iata][3:])
				
				if tracking + airport_flights < rand_idx:
					tracking += airport_flights
					selected_iata += 1
				elif tracking + airport_flights > rand_idx or tracking + airport_flights == rand_idx:
					tracking = rand_idx

			rand_flight = suitable_flights[rand_idx]
			flight_details(rand_flight, temp[selected_iata][:3])

# run main
if __name__ == '__main__':
>>>>>>> 238bca6 (v2.1.0 - Map update)
	main()