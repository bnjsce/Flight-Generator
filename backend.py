import json
import random
import secrets
import sys, os
import time
from datetime import datetime, timedelta
from pyflightdata import FlightData
from Flight import *

f = FlightData()

def get_base_data_dir():
	base = os.path.join(os.getenv('APPDATA'), 'FlightGenerator')
	os.makedirs(base, exist_ok=True)
	return base

CACHE_DIR = os.path.join(get_base_data_dir(), 'cache')

DEPARTURE_TTL = 3 * 60 # 3 mins
departure_cache = {}

METAR_CACHE_FILE = os.path.join(CACHE_DIR, 'metar_cache.json')
METAR_TTL = 30 # mins
metar_cache = {}

CONFIG_DIR = os.path.join(get_base_data_dir(), 'configs')
LOG_DIR = os.path.join(get_base_data_dir(), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'flight_log.json')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def load_departure_cache(iata):
	now = time.time()

	if iata in departure_cache:
		ts, data = departure_cache[iata]
		if now - ts < DEPARTURE_TTL:
			return data

	data = f.get_airport_departures(iata, limit=20, earlier_data=True)

	departure_cache[iata] = (now, data)
	return data

def latest_metar_cycle(dt):
	minute = dt.minute

	if minute < 30:
		dt = dt.replace(minute=0, second=0, microsecond=0)
	else:
		dt = dt.replace(minute=30, second=0, microsecond=0)

	return dt.isoformat()

def load_metar_cache():
	global metar_cache
	if os.path.exists(METAR_CACHE_FILE):
		with open(METAR_CACHE_FILE, 'r') as f:
			metar_cache = json.load(f)

def save_metar_cache():
	with open(METAR_CACHE_FILE, 'w') as f:
		f.write(json.dumps(metar_cache, indent=4))

def cleanup_metar_cache():
	now = time.time()
	to_delete = []

	for airport, entry in metar_cache.items():
		if now - entry['timestamp'] > METAR_TTL:
			to_delete.append(airport)

	for airport in to_delete:
		del metar_cache[airport]

def get_cached_metar(iata):
	now_dt = datetime.utcnow()
	now_ts = time.time()

	current_cycle = latest_metar_cycle(now_dt)

	if iata in metar_cache:
		entry = metar_cache[iata]

		cached_time = entry['timestamp']
		cached_cycle = entry.get('cycle')

		if cached_cycle == current_cycle:
			return entry['data']

		if now_ts - cached_time < METAR_TTL:
			if cached_cycle == current_cycle:
				return entry['data']

	data = f.get_airport_metars(iata)

	metar_cache[iata] = {
		'timestamp': now_ts,
		'cycle': current_cycle,
		'data': data
	}

	save_metar_cache()
	return data

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

def validate_airport(iata) -> bool:
	if len(f.get_airport_details(iata, limit=1)) > 0:
		return True
	else:
		return False

def validate_airline(icao) -> bool:
	if len(f.get_flights(icao)) > 0:
		return True
	else:
		return False

def validate_aircraft(icao) -> bool:
	valid_aircraft = {
		# Airbus
		'A318', 'A319', 'A19N', 'A320', 'A20N', 'A321', 'A21N',
		'A332', 'A333', 'A338', 'A339',
		'A343', 'A346', 'A388',

		# Boeing
		'B733', 'B734', 'B735', 'B736', 'B737', 'B738', 'B739',
		'B38M', 'B39M', 'B744', 'B748', 'B763',
		'B772', 'B77L', 'B77W', 'B788', 'B789', 'B78X',

		# Regional
		'E170', 'E175', 'E190', 'E195',
		'CRJ2', 'CRJ7', 'CRJ9', 'CRJX',

		# Turboprops
		'AT43', 'AT45', 'AT46', 'AT72', 'AT76',
		'DH8D', 'DH8A'
	}

	return icao in valid_aircraft

def get_random_flight(config_path) -> str or object:
	'''
	Randomly selects a flight based on user config data.
	'''
	cleanup_metar_cache()
	user_config = get_user_config(config_path)

	suitable_flights = []

	for i in range(len(user_config['airports'])):
		origin_iata = user_config['airports'][i]
		origin_departures = load_departure_cache(origin_iata)
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
					suitable_flights.append((flight, origin_iata))

	rand_flight = None
	if len(suitable_flights) == 0:
		return None

	rand_flight, origin_iata = secrets.choice(suitable_flights)
	return Flight(rand_flight, origin_iata, f.get_airport_details(origin_iata), get_cached_metar(origin_iata), get_cached_metar(rand_flight['airport']['destination']['code']['iata']))

def heading_diff(a, b):
	if a is None:
		return 0
	else:
		d = abs(a - b) % 360
		return min(d, 360 - d)

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
		"aircraft_icao": flight.aircraft_icao,
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
		save_flight_log(log)