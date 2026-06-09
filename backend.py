<<<<<<< HEAD
import json
import random
import secrets
import sys, os
from datetime import datetime
from pyflightdata import FlightData
from Flight import *

f = FlightData()

def get_base_data_dir():
	base = os.path.join(os.getenv('APPDATA'), 'FlightGenerator')
	os.makedirs(base, exist_ok=True)
	return base

CONFIG_DIR = os.path.join(get_base_data_dir(), 'configs')
LOG_DIR = os.path.join(get_base_data_dir(), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'flight_log.json')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def write_data(data, file_path) -> None:
	'''
	Write config data to config file.

	Parameters:
	data (list): List containing airport(s), airline(s), and plane(s).
	file_path (str): Path to JSON file.
	'''
	json_data = json.dumps(data, indent=4)
	with open(file_path, 'w') as f:
		f.write(json_data)

def validate_config(cfg) -> bool:
	'''
	Validates config file.

	Parameters:
	cfg (dict): Data from config file.

	Returns:
	(bool): True if valid, False if not.
	'''
	required = ['airports', 'airlines', 'aircraft', 'max_block_time']
	if len(cfg['airports']) > 6:
		return False
	if len(cfg['airlines']) > 8:
		return False
	if len(cfg['aircraft']) > 8:
		return False
	if not isinstance(cfg, dict):
		return False
	for key in required:
		if key not in cfg:
			return False
	if not isinstance(cfg['airports'], list):
		return False
	if not isinstance(cfg['airlines'], list):
		return False
	if not isinstance(cfg['aircraft'], list):
		return False
	if not isinstance(cfg['max_block_time'], int):
		return False

	return True

def get_user_config(config_path) -> dict:
	'''
	Retrieve user config file for search filter. Prompt user to set it up if path doesn't exist or file is empty.

	Parameters:
	config_path (str): File path for config file.

	Returns:
	temp (dict): {"airports": [AIRPORT1, AIRPORT2, ETC], "airlines": [AIRLINE1, AIRLINE2, ETC], "aircraft": [PLANE1, PLANE2, ETC], "max_block_time": x]
	'''
	data = None
	config_path = config_path # user input
	try:
		with open(config_path, 'r') as f:
			data = json.load(f)
	except:
		return {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}

	if not validate_config(data):
		return {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}
	else:
		return data

def get_random_flight(config_path) -> str or object:
	'''
	Randomly selects a flight based on user config data.
	'''
	user_config = get_user_config(config_path)

	suitable_flights = []

	temp = []
	for i in range(len(user_config['airports'])):
		origin_iata = user_config['airports'][i]
		origin_departures = f.get_airport_departures(origin_iata, limit=25, earlier_data=True)
		flight_count = 0
		for departure in origin_departures:
			accepted_airlines = user_config['airlines']
			accepted_aircraft = user_config['aircraft']
			flight = departure['flight']

			if any(flight['identification']['callsign'].startswith(prefix) for prefix in accepted_airlines) and flight['aircraft']['model']['code'] in accepted_aircraft:
				block_time = Flight.calc_flight_time(flight['time']['scheduled']['departure_time'], flight['time']['scheduled']['arrival_time']).split(' ')
				block_time_h = int(block_time[0].replace('h', ''))
				block_time_m = int(block_time[1].replace('m', ''))
				if block_time_h < int(user_config['max_block_time']) or (block_time_h == int(user_config['max_block_time']) and block_time_m == 0):
					suitable_flights.append(flight)
					flight_count += 1
		temp.append(f'{origin_iata}{flight_count}')

		rand_flight = None
		if len(suitable_flights) == 0:
			return None
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
			return Flight(rand_flight, temp[selected_iata][:3])

def get_flight_log():
	if not os.path.exists(LOG_FILE):
		return []

	try:
		with open(LOG_FILE, 'r') as f:
			return json.load(f)
	except:
		return []

def save_flight_log(data):
	with open(LOG_FILE, 'w') as f:
		json.dump(data, f, indent=4)

def add_flight_to_log(flight):
	log = get_flight_log()

	log.append({
		"date": datetime.now().strftime("%d/%m/%Y"),
		"aircraft": flight.aircraft_type,
		"callsign": flight.callsign,
		"departure": flight.departure_iata,
		"arrival": flight.arrival_iata,
		"distance": flight.distance,
		"block_time": flight.block_time
	})

	save_flight_log(log)

def delete_flight(index):
	log = get_flight_log()

	if 0 <= index < len(log):
		log.pop(index)
=======
import json
import random
import secrets
import sys, os
from datetime import datetime
from pyflightdata import FlightData
from Flight import *

f = FlightData()

def get_base_data_dir():
	base = os.path.join(os.getenv('APPDATA'), 'FlightGenerator')
	os.makedirs(base, exist_ok=True)
	return base

CONFIG_DIR = os.path.join(get_base_data_dir(), 'configs')
LOG_DIR = os.path.join(get_base_data_dir(), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'flight_log.json')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def write_data(data, file_path) -> None:
	'''
	Write config data to config file.

	Parameters:
	data (list): List containing airport(s), airline(s), and plane(s).
	file_path (str): Path to JSON file.
	'''
	json_data = json.dumps(data, indent=4)
	with open(file_path, 'w') as f:
		f.write(json_data)

def validate_config(cfg) -> bool:
	'''
	Validates config file.

	Parameters:
	cfg (dict): Data from config file.

	Returns:
	(bool): True if valid, False if not.
	'''
	required = ['airports', 'airlines', 'aircraft', 'max_block_time']
	if len(cfg['airports']) > 6:
		return False
	if len(cfg['airlines']) > 8:
		return False
	if len(cfg['aircraft']) > 8:
		return False
	if not isinstance(cfg, dict):
		return False
	for key in required:
		if key not in cfg:
			return False
	if not isinstance(cfg['airports'], list):
		return False
	if not isinstance(cfg['airlines'], list):
		return False
	if not isinstance(cfg['aircraft'], list):
		return False
	if not isinstance(cfg['max_block_time'], int):
		return False

	return True

def get_user_config(config_path) -> dict:
	'''
	Retrieve user config file for search filter. Prompt user to set it up if path doesn't exist or file is empty.

	Parameters:
	config_path (str): File path for config file.

	Returns:
	temp (dict): {"airports": [AIRPORT1, AIRPORT2, ETC], "airlines": [AIRLINE1, AIRLINE2, ETC], "aircraft": [PLANE1, PLANE2, ETC], "max_block_time": x]
	'''
	data = None
	config_path = config_path # user input
	try:
		with open(config_path, 'r') as f:
			data = json.load(f)
	except:
		return {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}

	if not validate_config(data):
		return {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}
	else:
		return data

def get_random_flight(config_path) -> str or object:
	'''
	Randomly selects a flight based on user config data.
	'''
	user_config = get_user_config(config_path)

	suitable_flights = []

	temp = []
	for i in range(len(user_config['airports'])):
		origin_iata = user_config['airports'][i]
		origin_departures = f.get_airport_departures(origin_iata, limit=25, earlier_data=True)
		flight_count = 0
		for departure in origin_departures:
			accepted_airlines = user_config['airlines']
			accepted_aircraft = user_config['aircraft']
			flight = departure['flight']

			if any(flight['identification']['callsign'].startswith(prefix) for prefix in accepted_airlines) and flight['aircraft']['model']['code'] in accepted_aircraft:
				block_time = Flight.calc_flight_time(flight['time']['scheduled']['departure_time'], flight['time']['scheduled']['arrival_time']).split(' ')
				block_time_h = int(block_time[0].replace('h', ''))
				block_time_m = int(block_time[1].replace('m', ''))
				if block_time_h < int(user_config['max_block_time']) or (block_time_h == int(user_config['max_block_time']) and block_time_m == 0):
					suitable_flights.append(flight)
					flight_count += 1
		temp.append(f'{origin_iata}{flight_count}')

		rand_flight = None
		if len(suitable_flights) == 0:
			return None
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
			return Flight(rand_flight, temp[selected_iata][:3])

def get_flight_log():
	if not os.path.exists(LOG_FILE):
		return []

	try:
		with open(LOG_FILE, 'r') as f:
			return json.load(f)
	except:
		return []

def save_flight_log(data):
	with open(LOG_FILE, 'w') as f:
		json.dump(data, f, indent=4)

def add_flight_to_log(flight):
	log = get_flight_log()

	log.append({
		"date": datetime.now().strftime("%d/%m/%Y"),
		"aircraft": flight.aircraft_type,
		"callsign": flight.callsign,
		"departure": flight.departure_iata,
		"arrival": flight.arrival_iata,
		"distance": flight.distance,
		"block_time": flight.block_time
	})

	save_flight_log(log)

def delete_flight(index):
	log = get_flight_log()

	if 0 <= index < len(log):
		log.pop(index)
>>>>>>> 238bca6 (v2.1.0 - Map update)
		save_flight_log(log)