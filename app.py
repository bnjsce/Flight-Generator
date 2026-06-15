from tkinter import *
import tkinter as tk
import tkinter.ttk as ttk
from tkintermapview import TkinterMapView
import threading
import time
import math
import sys
import re
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox
from backend import *

from SimConnect import *

TITLE = 'Flight Generator v2.3.2 | Ben Collingridge'
WIDTH = 860
HEIGHT = 890

def centre_window(window, width, height) -> None:
	'''
	Centre any main window.

	Parameters:
	window (tk.Frame): Window to be centred.
	width (int): Width of window.
	height (int): Height of window.
	'''
	window.update_idletasks()

	screen_width = window.winfo_screenwidth()
	screen_height = window.winfo_screenheight()

	x = (screen_width // 2) - (width // 2)
	y = (screen_height // 2) - (height // 2)

	window.geometry(f'{width}x{height}+{x}+{y}')

def resource_path(relative_path):
	if os.path.exists(os.path.join(os.path.dirname(sys.executable), relative_path)):
		base_path = os.path.dirname(sys.executable)
	else:
		base_path = os.path.abspath('.')
	return os.path.join(base_path, relative_path)

class App(tk.Tk):
	def __init__(self):
		'''
		Initialise app (root).
		'''
		super().__init__()

		load_metar_cache()

		self.title(TITLE)
		centre_window(self, WIDTH, HEIGHT)
		self.after(0, lambda: self.iconbitmap(resource_path('assets/app_icon.ico')))

		# container holds all pages
		container = tk.Frame(self)
		container.pack(fill='both', expand=True)

		self.frames = {}
		self.config_name = ''

		self.protocol('WM_DELETE_WINDOW', self.on_close)

		for F in (HomePage, EditConfig, NewConfig, FlightLog):
			frame = F(container, self)
			self.frames[F.__name__] = frame

		self.show_frame('HomePage')

	def on_close(self):
		home = self.frames.get('HomePage')

		if home and home.aircraft_update_job is not None:
			home.after_cancel(home.aircraft_update_job)

		self.destroy()

	def show_frame(self, name):
		'''
		Show different frame and hide current.

		Parameters:
		name (str): Name of frame to be shown.
		'''
		# hide current page (all pages)
		for frame in self.frames.values():
			frame.pack_forget()

		# show new page
		frame = self.frames[name]
		frame.pack(fill='both', expand=True)

		if hasattr(frame, 'load'):
			frame.load(self)

class HomePage(tk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)

		self.aircraft_update_job = None
		self.flight_active = False

		self.sim_connected = False
		self.sm = None
		self.aq = None

		self.aircraft_marker = None
		self.last_rendered_heading = 90
		self.heading_threshold = 5

		self.flight_details = None
		self.cooldown_active = False
		self.cooldown_seconds = 0

		self.departure_icon = ImageTk.PhotoImage(Image.open(resource_path('assets/green_pin.png')))
		self.arrival_icon = ImageTk.PhotoImage(Image.open(resource_path('assets/red_pin.png')))
		self.centre_dot_icon = ImageTk.PhotoImage(Image.open(resource_path('assets/centre_dot.png')))

		self.plane_icon_rotatable = Image.open(resource_path('assets/plane_icon.png'))
		self.plane_icon = ImageTk.PhotoImage(self.plane_icon_rotatable)
		self.last_icon = ImageTk.PhotoImage(self.plane_icon_rotatable)

		tk.Label(self, text='Flight Data', font=('Arial', 16)).pack(pady=(15, 5))
		
		config_row = tk.Frame(self)
		config_row.pack()

		# config controls
		self.config_text = tk.StringVar(value='Config: NONE')
		if controller.config_name != '':
			self.config_text.set(f'Config: {controller.config_name}')
		tk.Label(config_row, textvariable=self.config_text, font=('Arial', 12)).pack(side='left')
		tk.Button(config_row, text='EDIT', cursor='hand2', command=lambda: controller.show_frame('EditConfig') if controller.config_name != '' else messagebox.showinfo('No Config Selected', 'You have not selected a config file yet.')).pack(side='left', padx=(10, 0), ipadx=10)
		tk.Button(config_row, text='SELECT', cursor='hand2', command=lambda: self.replace_config(controller)).pack(side='left', padx=5, ipadx=10)
		tk.Button(config_row, text='NEW', cursor='hand2', command=lambda: controller.show_frame('NewConfig')).pack(side='left', padx=(0, 10), ipadx=10)

		# get flight controls
		flight_details = None
		flight_control_row = tk.Frame(self)
		flight_control_row.pack()
		self.get_flight_btn = tk.Button(flight_control_row, text='Get Flight!', cursor='hand2', command=lambda: self.create_flight_bridge(controller), bg='#c8f7c5')
		self.get_flight_btn.pack(ipadx=20, pady=(12, 0), side='left', padx=10)

		self.get_custom_flight_btn = tk.Button(flight_control_row, text='Get Flight from Arrival', cursor='hand2', command=lambda: self.create_flight_bridge(controller, from_arrival=True), bg='#c8f7c5')
		self.get_custom_flight_btn.pack(ipadx=20, pady=(12, 0), side='left', padx=10)

		self.simconnect_btn = tk.Button(flight_control_row, text='Start SimConnect', cursor='hand2', command=self.try_simconnect)
		self.simconnect_btn.pack(ipadx=20, pady=(12, 0), side='left', padx=10)

		tk.Button(flight_control_row, text='Stop SimConnect', cursor='hand2', command=self.handle_sim_disconnect).pack(ipadx=20, pady=(12, 0), side='left', padx=10)

		self.stop_active_flight_btn_text = tk.StringVar(value='No Flight Active')
		self.toggle_active_flight_btn = tk.Button(flight_control_row, text='No Flight Active', cursor='hand2', command=self.stop_active_flight)
		self.toggle_active_flight_btn.pack(ipadx=20, pady=(12, 0), side='left', padx=10)

		# create tabs for details and map
		self.notebook = ttk.Notebook(self)
		self.notebook.pack(fill='both', expand=True, pady=10)
		
		self.details_tab = tk.Frame(self.notebook)
		self.map_tab = tk.Frame(self.notebook)
		self.patch_notes_tab = tk.Frame(self.notebook)
		self.help_tab = tk.Frame(self.notebook)
		
		self.notebook.add(self.details_tab, text='Details')
		self.notebook.add(self.map_tab, text='Map')
		self.notebook.add(self.patch_notes_tab, text='Patch Notes')
		self.notebook.add(self.help_tab, text='HELP')

		self.map_widget = TkinterMapView(
			self.map_tab,
			width=800,
			height=515,
			cursor='tcross'
		)
		self.map_widget.pack(fill='x', padx=15, pady=10, anchor='w')
		self.map_widget.set_zoom(0)

		self.filter_buttons_row = tk.Frame(self.map_tab)
		self.filter_buttons_row.pack(fill='both', side='right')

		self.tracking_row = tk.Frame(self.map_tab)
		self.tracking_row.pack(fill='both', side='left')

		self.path_visible = True
		self.pins_visible = True
		self.follow_aircraft = False

		tk.Button(self.filter_buttons_row, text='Centre Route', cursor='hand2', command=lambda: self.draw_static_map(self.flight_details) if self.flight_details else self.map_widget.set_zoom(0)).pack(ipadx=31, pady=(8, 0), padx=100)
		tk.Button(self.filter_buttons_row, text='Centre Aircraft', cursor='hand2', command=lambda: self.draw_static_map(self.flight_details, recentre=True) if self.flight_details else self.map_widget.set_zoom(0)).pack(ipadx=27, pady=(8, 0), padx=100)
		self.follow_aircraft_btn = tk.Button(self.filter_buttons_row, text='Follow Aircraft', cursor='target', bg='#f7c5c5', command=lambda: self.toggle_map_widgets(self.path_visible, self.pins_visible, not self.follow_aircraft))
		self.follow_aircraft_btn.pack(ipadx=27, pady=(8, 0), padx=100)
		tk.Button(self.filter_buttons_row, text='Toggle Path', cursor='hand2', command=lambda: self.toggle_map_widgets(not self.path_visible, self.pins_visible, self.follow_aircraft)).pack(ipadx=33, pady=(8, 0), padx=100)
		tk.Button(self.filter_buttons_row, text='Toggle Pins', cursor='hand2', command=lambda: self.toggle_map_widgets(self.path_visible, not self.pins_visible, self.follow_aircraft)).pack(ipadx=33, pady=(8, 0), padx=100)

		# SimConnect tracking UI
		self.live_altitude = tk.StringVar(value='Altitude (MSL): N/A')
		self.live_heading = tk.StringVar(value='Heading: N/A')
		self.live_airspeed = tk.StringVar(value='Airspeed: N/A')
		self.live_ground_speed = tk.StringVar(value='Ground Speed: N/A')
		self.live_vertical_speed = tk.StringVar(value='Vertical Speed: N/A')
		self.live_wind = tk.StringVar(value='Wind: N/A')
		self.live_grounded = tk.StringVar(value='On ground: N/A')

		tk.Label(self.tracking_row, textvariable=self.live_altitude, font=('Arial', 13)).pack(anchor='e', padx=100, pady=(2, 0))
		tk.Label(self.tracking_row, textvariable=self.live_heading, font=('Arial', 13)).pack(anchor='e', padx=100)
		tk.Label(self.tracking_row, textvariable=self.live_airspeed, font=('Arial', 13)).pack(anchor='e', padx=100)
		tk.Label(self.tracking_row, textvariable=self.live_ground_speed, font=('Arial', 13)).pack(anchor='e', padx=100)
		tk.Label(self.tracking_row, textvariable=self.live_vertical_speed, font=('Arial', 13)).pack(anchor='e', padx=100)
		tk.Label(self.tracking_row, textvariable=self.live_wind, font=('Arial', 13)).pack(anchor='e', padx=100)
		tk.Label(self.tracking_row, textvariable=self.live_grounded, font=('Arial', 13)).pack(anchor='e', padx=100)

		# PATCH NOTES
		tk.Label(self.patch_notes_tab, text='v2.3.2', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Added active flight toggle after clicking fly now.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='v2.3.1', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- You can now generate a flight from your arrival airport.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='v2.3.0', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Added METAR and departure caching to speed up flight generation.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- METAR will update if new cycle or last cache was longer than 30 minutes ago.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Departure cache will update if new departure airport or last cache was longer than 3 minutes.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='v2.2.1', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Fixed SimConnect map issues.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Added refresh and disconnect SimConnect buttons.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- SimConnect no longer tries to automatically launch after generating a flight.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- For live aircraft traffic, you must now click the start SimConnect button.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Added map controls and filters for more customisable interface.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='v2.2.0 (Major Update)', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Added SimConnect support.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- This means when your simulator is open, you will see your aircraft on the map.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- The map will reflect your aircraft position and heading.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.patch_notes_tab, text='- Underneath the map, it shows live flight information such as altitude and IAS.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))

		# HELP PAGE
		tk.Label(self.help_tab, text='Airport Validation', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.help_tab, text='- When entering an airport, you must use the IATA (3 letters).', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- For example: London Heathrow would be LHR, Paris Charles-de-Gaulle would be CDG, etc.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- You can use lowercase, uppercase, or a mix if you really want to; as long as it is a valid IATA.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='Airline Validation', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.help_tab, text='- When entering an airline, you must use the ICAO (3 letters/numbers).', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- For example: British Airways would be BAW, easyJet would be EZY, etc.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- Again, you can use lowercase, uppercase, or a mix if you really want to; as long as it is a valid ICAO.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='Aircraft Validation', font=('Arial', 14, 'bold')).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.help_tab, text='- When entering an aircraft, you must use the ICAO (4 letters/numbers).', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- For example: Airbus A321 NEO would be A21N, Boeing 777-300ER would be B77W, etc.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- You can use lowercase, uppercase, or a mix; as long as it is a valid ICAO.', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))
		tk.Label(self.help_tab, text='- Unfortunately, there is no easy way to validate this, so below are the accepted aircraft:', font=('Arial', 11)).pack(anchor='w', pady=5, padx=(10, 0))

		self.aircraft_table = ttk.Notebook(self.help_tab)
		self.aircraft_table.pack(fill='both', expand=True, pady=10)

		self.airbus_tab = tk.Frame(self.aircraft_table)
		self.boeing_tab = tk.Frame(self.aircraft_table)
		self.regional_tab = tk.Frame(self.aircraft_table)

		self.aircraft_table.add(self.airbus_tab, text='Airbus')
		self.aircraft_table.add(self.boeing_tab, text='Boeing')
		self.aircraft_table.add(self.regional_tab, text='Regional / Turboprop')

		# airbus
		tk.Label(self.airbus_tab, text='A318, A319, A19N (A319neo), A320, A20N (A320neo), A321, A21N (A321neo), A332 (A330-200), A333 (A330-300)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.airbus_tab, text='A338 (A330-800neo), A339 (A330-900neo), A343 (A340-300), A346 (A340-600), A388 (A380)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))

		# boeing
		tk.Label(self.boeing_tab, text='B733 (737-300), B734 (737-400), B735 (737-500), B736 (737-600), B737 (737-700), B738 (737-800), B739 (737-900)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.boeing_tab, text='B38M (737 MAX 8), B39M (737 MAX 9), B744 (747-400), B748 (747-8)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.boeing_tab, text='B763 (767-300), B772 (777-200), B77L (777-200LR), B77W (777-300ER), B788 (787-8), B789 (787-9), B78X (787-10)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))

		# regional/turboprop/commuter
		tk.Label(self.regional_tab, text='E170, E175, E190, E195', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.regional_tab, text='CRJ2 (CRJ-200), CRJ7 (CRJ-700), CRJ9 (CRJ-900), CRJX (CRJ-1000)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.regional_tab, text='AT43, AT45, AT46, AT72, AT76 (entire ATR family basically)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))
		tk.Label(self.regional_tab, text='DH8D (Dash 8 Q400), DH8A (Dash 8 series variants sometimes grouped)', font=('Arial', 11)).pack(anchor='w', pady=10, padx=(10, 0))

		# INITIALISE FLIGHT INFO DISPLAY
		# identification
		self.callsign = tk.StringVar(value='Callsign: ')
		self.aircraft_type = tk.StringVar(value='Aircraft: ')
		# departure info
		self.departure_name = tk.StringVar(value='Departure: ')
		self.departure_icao_iata = tk.StringVar(value='ICAO/IATA: ')
		self.departure_terminal = tk.StringVar(value='Terminal: ')
		self.departure_gate = tk.StringVar(value='Gate: ')
		# arrival info
		self.arrival_name = tk.StringVar(value='Arrival: ')
		self.arrival_icao_iata = tk.StringVar(value='ICAO/IATA: ')
		self.arrival_terminal = tk.StringVar(value='Terminal: ')
		self.arrival_gate = tk.StringVar(value='Gate: ')
		# flight info
		self.distance = tk.StringVar(value='Distance: ')
		self.block_time = tk.StringVar(value='Est. Block time: ')
		# metar report
		self.departure_metar = tk.StringVar(value='DEP METAR')
		self.arrival_metar = tk.StringVar(value='ARR METAR')

		# identification
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=(20, 3))
		tk.Label(self.details_tab, text='IDENTIFICATION', font=('Arial', 14, 'bold')).pack(pady=3)
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, textvariable=self.callsign, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.aircraft_type, font=('Arial', 12)).pack(pady=3)
		# departure info
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, text='DEPARTURE INFO', font=('Arial', 14, 'bold')).pack(pady=3)
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, textvariable=self.departure_name, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.departure_icao_iata, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.departure_terminal, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.departure_gate, font=('Arial', 12)).pack(pady=3)
		# arrival info
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, text='ARRIVAL INFO', font=('Arial', 14, 'bold')).pack(pady=3)
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, textvariable=self.arrival_name, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.arrival_icao_iata, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.arrival_terminal, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.arrival_gate, font=('Arial', 12)).pack(pady=3)
		# flight info
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, text='FLIGHT INFO', font=('Arial', 14, 'bold')).pack(pady=3)
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, textvariable=self.distance, font=('Arial', 12)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.block_time, font=('Arial', 12)).pack(pady=3)
		# metar report
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, text='METAR REPORT', font=('Arial', 14, 'bold')).pack(pady=3)
		ttk.Separator(self.details_tab, orient='horizontal').pack(fill='x', padx=30, pady=3)
		tk.Label(self.details_tab, textvariable=self.departure_metar, font=('Arial', 10)).pack(pady=3)
		tk.Label(self.details_tab, textvariable=self.arrival_metar, font=('Arial', 10)).pack(pady=3)

		nav = tk.Frame(self.details_tab)
		nav.pack()
		tk.Button(nav, text='Fly now', cursor='hand2', command=lambda: self.fly_now() if self.flight_details != None else controller.show_frame('HomePage')).pack(ipadx=15, pady=(8, 0), side='left', padx=5)
		tk.Button(nav, text='Flight log', cursor='hand2', command=lambda: controller.show_frame('FlightLog')).pack(ipadx=15, pady=(8, 0), side='left', padx=5)

	def load(self, controller):
		'''
		Refresh window.
		'''
		if controller.config_name:
			self.config_text.set(f'Config: {os.path.basename(controller.config_name)}')
		else:
			self.config_text.set('Config: NONE')

		try:
			self.sm = SimConnect()
			self.aq = AircraftRequests(self.sm)
			self.sim_connected = True
		except:
			self.sim_connected = False

	def create_flight_bridge(self, controller, from_arrival=False):
		if not self.flight_active:
			if controller.config_name != '':
				if not from_arrival:
					self.create_flight(controller)
				else:
					self.create_flight(controller, custom=True)
			else:
				controller.show_frame('HomePage')
		else:
			return messagebox.showinfo('Flight Active', 'Please stop your current flight to generate a new one.')

	def stop_active_flight(self):
		self.flight_active = False
		self.toggle_active_flight_btn.config(
			text=f'No Flight Active',
			bg='white',
		)

	def try_simconnect(self):
		if self.sm is not None:
			self.sm.exit()
		self.sm = None
		self.aq = None
		self.sim_connected = False

		if self.aircraft_marker:
			self.aircraft_marker.delete()
			self.aircraft_marker = None

		try:
			self.sm = SimConnect()
			self.aq = AircraftRequests(self.sm)
			self.sim_connected = True
		except:
			self.sim_connected = False

		self.update_aircraft()

	def replace_config(self, controller):
		'''
		Select a config file via native file explorer.
		'''
		filename = filedialog.askopenfilename(
			initialdir=CONFIG_DIR,
			title='Select a configuration file',
			filetypes=(
				('JSON files', '*.json'),
				('All files', '*.*')
			)
		)

		if not filename:
			return

		controller.config_name = filename
		self.config_text.set(f'Config: {os.path.basename(filename)}')

	def fly_now(self):
		if self.flight_details is None:
			return messagebox.showinfo('No Flight', 'Generate a flight first.')

		add_flight_to_log(self.flight_details)
		self.flight_active = True
		self.toggle_active_flight_btn.config(
			text=f'Stop Active Flight',
			bg='#f7c5c5'
		)
		messagebox.showinfo('Flight Logged', 'Flight added to logbook.')

	def start_cooldown_ui(self, seconds=5):
		self.cooldown_active = True
		self.cooldown_seconds = seconds

		def tick(remaining):
			if remaining <= 0:
				self.reset_button()
				return

			self.get_flight_btn.config(
				text=f'Cooldown: {remaining}s',
				bg='#f7c5c5',
				cursor='watch'
			)
			self.get_custom_flight_btn.config(
				text=f'Cooldown: {remaining}s',
				bg='#f7c5c5',
				cursor='watch'
			)

			self.after(1000, lambda: tick(remaining - 1))

		tick(seconds)

	def reset_button(self):
		self.cooldown_active = False
		self.cooldown_seconds = 0

		self.get_flight_btn.config(
			bg='#c8f7c5',
			text='Get Flight!',
			cursor='hand2'
		)
		self.get_custom_flight_btn.config(
			bg='#c8f7c5',
			text='Get Flight from Arrival',
			cursor='hand2'
		)

	def create_flight(self, controller, custom=False):
		'''
		Create Flight object storing information on a randomly selected flight,
		based on parameters defined by the selected config file.
		'''
		if self.cooldown_active:
			return

		self.cooldown_active = True

		self.get_flight_btn.config(text='Getting flight...', bg='#698bf0', cursor='watch')
		self.get_custom_flight_btn.config(text='Getting flight...', bg='#698bf0', cursor='watch')

		def task():
			try:
				config = get_user_config(controller.config_name)

				if not config:
					raise ValueError('There is an error with the selected config file.')

				flight = None
				if not custom:
					flight = get_random_flight(controller.config_name)
				else:
					custom_data = {
						'departure_iata': self.flight_details.arrival_iata,
						'airline': self.flight_details.callsign[:3]
					}
					flight = get_random_flight(controller.config_name, custom_data=custom_data)
				if flight is None:
					raise ValueError('No valid flights could be generated. Check your config file or try again later.')
					self.get_flight_btn.config(text='Get Flight!')
					self.get_custom_flight_btn.config(text='Get Flight from Arrival')
				self.after(0, lambda: self.finish_ui_update(flight, custom=True))
			except Exception as e:
				self.after(0, lambda: messagebox.showerror('Error', str(e)))
				self.after(0, self.reset_button)

		threading.Thread(target=task, daemon=True).start()

	def finish_ui_update(self, f, custom=False):
		'''
		Update flight info display.
		'''
		self.flight_details = f

		self.get_flight_btn.config(text='Get Flight!')
		self.get_custom_flight_btn.config(text='Get Flight from Arrival')

		# identification
		self.callsign.set(f'Callsign: {f.callsign}')
		self.aircraft_type.set(f'Aircraft: {f.aircraft_type}')
		# departure info
		self.departure_name.set(f'Departure: {f.departure_name}')
		self.departure_icao_iata.set(f'ICAO/IATA: {f.departure_icao}/{f.departure_iata}')
		self.departure_terminal.set(f'Terminal: {f.departure_terminal}')
		self.departure_gate.set(f'Gate: {f.departure_gate}')
		# arrival info
		self.arrival_name.set(f'Arrival: {f.arrival_name}')
		self.arrival_icao_iata.set(f'ICAO/IATA: {f.arrival_icao}/{f.arrival_iata}')
		self.arrival_terminal.set(f'Terminal: {f.arrival_terminal}')
		self.arrival_gate.set(f'Gate: {f.arrival_gate}')
		# flight info
		self.distance.set(f'Distance: {f.distance} NM')
		self.block_time.set(f'Est. Block time: {f.block_time}')
		# metar report
		self.departure_metar.set(f.departure_metar)
		self.arrival_metar.set(f.arrival_metar)

		self.draw_static_map(f)
		self.start_cooldown_ui(5)

	def handle_sim_disconnect(self):
		self.sim_connected = False

		if self.aircraft_update_job:
			self.after_cancel(self.aircraft_update_job)
			self.aircraft_update_job = None

		if self.aircraft_marker:
			self.aircraft_marker.delete()
			self.aircraft_marker = None

		self.live_altitude.set('Altitude (MSL): N/A')
		self.live_heading.set('Heading: N/A')
		self.live_airspeed.set('Airspeed: N/A')
		self.live_ground_speed.set('Ground Speed: N/A')
		self.live_vertical_speed.set('Vertical Speed: N/A')
		self.live_wind.set('Wind: N/A')
		self.live_grounded.set('On ground: N/A')

		try:
			self.sm.exit()
		except:
			pass

		self.sm = None
		self.aq = None
		self.simconnect_btn.config(text='Start SimConnect')
		self.draw_static_map(self.flight_details)

	def get_rotated_plane_icon(self, heading):
		rotated = self.plane_icon_rotatable.rotate(
			-(heading - 90),
			resample=Image.BICUBIC,
			expand=True
		)
		self.last_rendered_heading = heading
		return ImageTk.PhotoImage(rotated)

	def update_aircraft(self):
		if not self.sim_connected:
			self.simconnect_btn.config(text='Start SimConnect')
			if self.aircraft_marker is not None:
				self.aircraft_marker.delete()
			self.aircraft_marker = None
			messagebox.showerror('SimConnect Error', 'Could not connect to simulator.')
			return

		self.simconnect_btn.config(text='Refresh SimConnect')

		try:
			live_data = {
				'lat': self.aq.get('PLANE_LATITUDE'),
				'lon': self.aq.get('PLANE_LONGITUDE'),
				'heading': math.degrees(self.aq.get('PLANE_HEADING_DEGREES_TRUE')),
				'altitude': math.floor(self.aq.get('PLANE_ALTITUDE')),
				'airspeed': math.floor(self.aq.get('AIRSPEED_INDICATED')),
				'ground_speed': math.floor(self.aq.get('GROUND_VELOCITY')),
				'vertical_speed': math.floor(self.aq.get('VERTICAL_SPEED')),
				'wind_direction': self.aq.get('AMBIENT_WIND_DIRECTION'),
				'wind_speed': math.floor(self.aq.get('AMBIENT_WIND_VELOCITY')),
				'on_ground': 'Yes' if self.aq.get('SIM_ON_GROUND') == 1 else 'No'
			}
		except Exception:
			self.handle_sim_disconnect()
			return

		self.live_lat = live_data['lat']
		self.live_lon = live_data['lon']
		heading = live_data['heading']
		icon = self.last_icon

		self.live_altitude.set(f"Altitude (MSL): {live_data['altitude']} ft")
		if heading is not None:
			self.live_heading.set(f"Heading: {heading:03.0f}°")
		else:
			self.live_heading.set(f"Heading: N/A")
		self.live_airspeed.set(f"Airspeed: {live_data['airspeed']} kts")
		self.live_ground_speed.set(f"Ground Speed: {live_data['ground_speed']} kts")
		self.live_vertical_speed.set(f"Vertical Speed: {live_data['vertical_speed']} fpm")
		self.live_wind.set(f"Wind: {live_data['wind_direction']:03.0f}° @ {live_data['wind_speed']} kts")
		self.live_grounded.set(f"On ground: {live_data['on_ground']}")

		if self.aircraft_marker is not None:
			self.aircraft_marker.delete()
		if isinstance(self.live_lat, (int, float)) and isinstance(self.live_lon, (int, float)):
			# CREATE ICON
			if isinstance(heading, (int, float)):
				icon = self.get_rotated_plane_icon(heading)
				self.last_rendered_heading = heading
			else:
				icon = self.plane_icon

			# CREATE/UPDATE MARKER
			if self.aircraft_marker is None:
				self.aircraft_marker = self.map_widget.set_marker(
					self.live_lat, self.live_lon,
					text='',
					icon=self.plane_icon
				)
			else:
				self.aircraft_marker.delete()
				self.aircraft_marker = self.map_widget.set_marker(
					self.live_lat, self.live_lon,
					text='',
					icon=self.last_icon
				)

			if self.follow_aircraft:
				self.map_widget.set_position(self.live_lat, self.live_lon)

		self.last_icon = icon
		self.aircraft_update_job = self.after(500, self.update_aircraft)

	def toggle_map_widgets(self, path, pins, aircraft):
		self.path_visible = path
		self.pins_visible = pins
		self.follow_aircraft = aircraft
		if self.follow_aircraft:
			self.follow_aircraft_btn.config(text='Following Aircraft...', bg='#c8f7c5')
		else:
			self.follow_aircraft_btn.config(text='Follow Aircraft', bg='#f7c5c5')

		if aircraft:
			self.draw_static_map(self.flight_details, recentre=True)
		else:
			self.draw_static_map(self.flight_details)

	def get_map_centre(self, aircraft=False):
		lat = 0
		lon = 0
		if self.flight_details:
			if aircraft and self.sim_connected:
				lat = self.live_lat
				lon = self.live_lon
			elif not aircraft or (aircraft and not self.sim_connected):
				lat = (self.flight_details.departure_coords[0] + self.flight_details.arrival_coords[0]) / 2
				lon = (self.flight_details.departure_coords[1] + self.flight_details.arrival_coords[1]) / 2

		return (lat, lon)

	def draw_static_map(self, f, recentre=False):
		self.map_widget.delete_all_marker()
		self.map_widget.delete_all_path()

		def calculate_zoom(dep, arr):
			lat_span = abs(dep[0] - arr[0])
			lon_span = abs(dep[1] - arr[1])
			span = max(lat_span, lon_span)

			if span == 0:
				return 10

			zoom = int(8 - math.log2(span))
			return max(2, min(10, zoom)) + 1

		route_centre_coords = self.get_map_centre()
		centre_coords = route_centre_coords
		zoom = 0
		if self.flight_details:
			zoom = calculate_zoom(f.departure_coords, f.arrival_coords)
		if recentre:
			zoom = 8
			centre_coords = self.get_map_centre(aircraft=True)

		centre_lat = centre_coords[0]
		centre_lon = centre_coords[1]
		self.map_widget.set_position(centre_lat, centre_lon)
		self.map_widget.set_zoom(zoom)

		self.map_widget.update_idletasks()

		if not self.flight_details:
			return

		if self.pins_visible:
			self.map_widget.set_marker(
				f.departure_coords[0],
				f.departure_coords[1],
				text=f'{f.departure_iata}\n{f.departure_timezone} ({f.departure_time_offset})',
				icon=self.departure_icon
			)
			self.map_widget.set_marker(
				f.arrival_coords[0],
				f.arrival_coords[1],
				text=f'{f.arrival_iata}\n{f.arrival_timezone} ({f.arrival_time_offset})',
				icon=self.arrival_icon
			)

			heading = f.calc_heading(f.departure_coords, f.arrival_coords)
			label = f'{f.distance} NM\nHDG {heading:03.0f}°'

			self.map_widget.set_marker(
				route_centre_coords[0],
				route_centre_coords[1],
				text=label,
				icon=self.centre_dot_icon
			)

		if self.path_visible:
			self.map_widget.set_path(
				[f.departure_coords, f.arrival_coords],
				width=2,
				color='dodgerblue'
			)

class BaseConfigEditor(tk.Frame):
	def __init__(self, parent, controller):
		'''
		Parent class to be inherited by EditConfig and NewConfig.
		'''
		super().__init__(parent)
		self.controller = controller

		self.config_data = {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}

		tk.Label(self, text='Note: you can double click to edit an item.', font=('Arial', 12), pady=10).pack()

		# data entry fields
		self._build_section('Airports', 'airports', 6, is_airport=True)
		self._build_section('Airlines', 'airlines', 8, is_airline=True)
		self._build_section('Aircraft', 'aircraft', 8, is_aircraft=True)

		tk.Label(self, text='Max Block Time (hours)').pack()

		# min 1 hour max 24 hours
		self.block_time = tk.StringVar(value='1')
		ttk.Combobox(
			self,
			textvariable=self.block_time,
			values=[str(i) for i in range(1, 25)],
			state='readonly'
		).pack()

		# save/cancel (overridden behaviour via methods)
		tk.Button(self, text=self.save_text(), cursor='hand2', command=self.save_config).pack(pady=10)
		tk.Button(self, text='Cancel', cursor='hand2', command=lambda: controller.show_frame('HomePage')).pack()

	# UI BUILDER
	def _build_section(self, title, key, limit, is_airport=False, is_airline=False, is_aircraft=False):
		'''
		Build data entry fields and associated UI.
		'''
		tk.Label(self, text=title).pack()

		listbox = tk.Listbox(self, height=6 if key == 'airports' else 8)
		listbox.pack()

		entry = tk.Entry(self)
		entry.pack()

		# press enter to add item
		entry.bind(
			'<Return>',
			lambda e: self.add_item(entry, listbox, key, limit)
		)

		if title.lower() == 'aircraft':
			tk.Button(
				self,
				text=f'Add {title}',
				cursor='hand2',
				command=lambda: self.add_item(entry, listbox, key, limit)
			).pack()
		else:
			tk.Button(
				self,
				text=f'Add {title[:-1]}',
				cursor='hand2',
				command=lambda: self.add_item(entry, listbox, key, limit)
			).pack()

		tk.Button(
			self,
			text='Remove Selected',
			cursor='hand2',
			command=lambda: self.remove_item(listbox, key)
		).pack()

		# double click an item to edit
		listbox.bind(
			'<Double-Button-1>',
			lambda e: self.edit_item(listbox, key)
		)

		setattr(self, f"{key}_list", listbox)

	# CORE LOGIC

	def add_item(self, entry, listbox, key, limit):
		'''
		Add valid item to listbox.

		Parameters:
		entry (tk.Entry): Data to be appended.
		listbox (tk.Listbox): Listbox to be appended to.
		key (str): Data field key identifier.
		limit (int): Maximum number of entries allowed in listbox.
		'''
		value = entry.get().strip().upper()

		# no value entered
		if not value:
			return

		if len(self.config_data[key]) >= limit:
			return messagebox.showinfo('Limit Reached', f'{key} limit reached')

		# validation
		if key == 'airports' and (not value.isalpha() or len(value) > 3):
			return messagebox.showinfo('Invalid Entry', 'Airport must be 3 letters (IATA) eg. LHR = London Heathrow')
		if key == 'airlines' and (not value.isalnum() or len(value) > 3):
			return messagebox.showinfo('Invalid Entry', 'Airline must be 3 letters/numbers (ICAO) eg. BAW = British Airways')
		if key == 'aircraft' and (not value.isalnum() or len(value) > 4):
			return messagebox.showinfo('Invalid Entry', 'Aircraft must be 4 letters/numbers (ICAO) eg. A20N = A320 NEO')

		if key == 'airports' and not validate_airport(value):
			return messagebox.showinfo('Invalid Entry', 'Airport not found.')
		if key == 'airlines' and not validate_airline(value):
			return messagebox.showinfo('Invalid Entry', 'Airline not found.')
		if key == 'aircraft' and not validate_aircraft(value):
			return messagebox.showinfo('Invalid Entry', 'Aircraft not found.')

		if value in self.config_data[key]:
			return messagebox.showinfo('Duplicate Entry', f'{value} already exists in your config.')

		# add data to config and listbox
		self.config_data[key].append(value)
		listbox.insert(tk.END, value)

		entry.delete(0, tk.END)
		entry.focus_set()
		self.flash_entry(entry) # visual confirmation

	def remove_item(self, listbox, key):
		'''
		Remove an item from a listbox.
		'''
		sel = listbox.curselection()
		if not sel:
			return

		index = sel[0]
		value = listbox.get(index)

		if value in self.config_data[key]:
			self.config_data[key].remove(value)

		listbox.delete(index)

	def edit_item(self, listbox, key):
		'''
		Double click to edit an item in any listbox.
		'''
		sel = listbox.curselection()
		if not sel:
			return

		index = sel[0]
		old = listbox.get(index)

		popup = tk.Toplevel(self)
		popup.title('Edit Item')
		popup.resizable(False, False)
		popup.transient(self)
		popup.grab_set()
		centre_window(popup, 250, 100)

		entry = tk.Entry(popup)
		entry.insert(0, old)
		entry.pack(pady=15)
		entry.focus_set()

		def save():
			new = entry.get().strip().upper()
			if not new:
				return

			# validation
			if key == 'airports' and (not new.isalpha() or len(new) > 3):
				return messagebox.showinfo('Invalid Entry', 'Airport must be 3 letters (IATA) eg. LHR = London Heathrow')
			if key == 'airlines' and (not new.isalnum() or len(new) > 3):
				return messagebox.showinfo('Invalid Entry', 'Airline must be 3 letters/numbers (ICAO) eg. BAW = British Airways')
			if key == 'aircraft' and (not new.isalnum() or len(new) > 4):
				return messagebox.showinfo('Invalid Entry', 'Aircraft must be 4 letters/numbers (ICAO) eg. A20N = A320 NEO')

			if key == 'airports' and not validate_airport(new):
				return messagebox.showinfo('Invalid Entry', 'Airport not found.')
			if key == 'airlines' and not validate_airline(new):
				return messagebox.showinfo('Invalid Entry', 'Airline not found.')
			if key == 'aircraft' and not validate_aircraft(new):
				return messagebox.showinfo('Invalid Entry', 'Aircraft not found.')

			if new in self.config_data[key]:
				return messagebox.showinfo('Duplicate Entry', f'{new} already exists in your config.')

			self.config_data[key][index] = new
			listbox.delete(index)
			listbox.insert(index, new)
			popup.destroy()

		# press enter to save edits
		entry.bind('<Return>', lambda e: save())
		tk.Button(popup, text='Save', cursor='hand2', command=save).pack()

	# HOOKS

	def flash_entry(self, entry):
		'''
		Flash entry to show valid data addition to listbox.
		'''
		entry.config(bg='#c8f7c5') # light green
		self.after(240, lambda: entry.config(bg='white'))

	def save_text(self):
		return 'Save'

	def load(self, controller):
		pass

	def save_config(self):
		pass

class EditConfig(BaseConfigEditor):
	def load(self, controller):
		self.config_data = get_user_config(controller.config_name)

		# prevents duplicate data
		self.airports_list.delete(0, tk.END)
		self.airlines_list.delete(0, tk.END)
		self.aircraft_list.delete(0, tk.END)

		# add config data to display
		for x in self.config_data['airports']:
			self.airports_list.insert(tk.END, x)

		for x in self.config_data['airlines']:
			self.airlines_list.insert(tk.END, x)

		for x in self.config_data['aircraft']:
			self.aircraft_list.insert(tk.END, x)

		self.block_time.set(str(self.config_data['max_block_time']))

	def save_config(self):
		self.config_data['max_block_time'] = int(self.block_time.get())
		write_data(self.config_data, self.controller.config_name)
		self.controller.show_frame('HomePage')

	def save_text(self):
		return "Save Config"

class NewConfig(BaseConfigEditor):
	def load(self, controller):
		# empty config sheet
		self.config_data = {
			"airports": [],
			"airlines": [],
			"aircraft": [],
			"max_block_time": 1
		}

		for lst in [self.airports_list, self.airlines_list, self.aircraft_list]:
			lst.delete(0, tk.END)

		self.block_time.set('1')

	def save_config(self):
		self.config_data['max_block_time'] = int(self.block_time.get())

		filename = filedialog.asksaveasfilename(
			initialdir=CONFIG_DIR,
			defaultextension='.json',
			filetypes=[('JSON files', '*.json')]
		)

		if not filename:
			return

		write_data(self.config_data, filename)

		self.controller.config_name = filename
		self.controller.show_frame('HomePage')

	def save_text(self):
		return 'Create Config'

class FlightLog(tk.Frame):
	def __init__(self, parent, controller):
		super().__init__(parent)

		style = ttk.Style()
		style.configure(
			'Treeview.Heading',
			font=('Segoe UI', 10, 'bold')
		)

		self.notebook = ttk.Notebook(self)
		self.notebook.pack(fill='both', expand=True, pady=20)
		self.logbook_tab = tk.Frame(self.notebook)
		self.stats_tab = tk.Frame(self.notebook)
		self.notebook.add(self.logbook_tab, text='Logbook')
		self.notebook.add(self.stats_tab, text='Stats')

		# FILTERS
		filter_frame = tk.Frame(self.logbook_tab)
		filter_frame.pack(pady=10)

		tk.Label(filter_frame, text='Departure').grid(row=0, column=0)
		tk.Label(filter_frame, text='Arrival').grid(row=0, column=1)
		tk.Label(filter_frame, text='Aircraft').grid(row=0, column=2)
		tk.Label(filter_frame, text='Airline').grid(row=0, column=3)

		self.dep_filter = tk.StringVar(value='All')
		self.arr_filter = tk.StringVar(value='All')
		self.aircraft_filter = tk.StringVar(value='All')
		self.airline_filter = tk.StringVar(value='All')

		self.dep_combo = ttk.Combobox(
			filter_frame,
			textvariable=self.dep_filter,
			width=10,
			state='readonly'
		)

		self.arr_combo = ttk.Combobox(
			filter_frame,
			textvariable=self.arr_filter,
			width=10,
			state='readonly'
		)

		self.aircraft_combo = ttk.Combobox(
			filter_frame,
			textvariable=self.aircraft_filter,
			width=10,
			state='readonly'
		)

		self.airline_combo = ttk.Combobox(
			filter_frame,
			textvariable=self.airline_filter,
			width=10,
			state='readonly'
		)

		self.dep_combo.grid(row=1, column=0)
		self.arr_combo.grid(row=1, column=1)
		self.aircraft_combo.grid(row=1, column=2)
		self.airline_combo.grid(row=1, column=3)

		tk.Button(
			filter_frame,
			text='Apply',
			cursor='hand2',
			command=self.apply_filters
		).grid(row=1, column=4, padx=5)

		tk.Button(
			filter_frame,
			text='Clear',
			cursor='hand2',
			command=self.clear_filters
		).grid(row=1, column=5)

		# TREEVIEW
		columns = (
			'date',
			'aircraft',
			'callsign',
			'departure',
			'arrival',
			'distance',
			'block_time'
		)

		self.tree = ttk.Treeview(
			self.logbook_tab,
			columns=columns,
			show='headings',
			height=20
		)

		self.tree.heading('date', text='Date', anchor='w')
		self.tree.heading('aircraft', text='Aircraft', anchor='w')
		self.tree.heading('callsign', text='Callsign', anchor='w')
		self.tree.heading('departure', text='Departure', anchor='w')
		self.tree.heading('arrival', text='Arrival', anchor='w')
		self.tree.heading('distance', text='Distance', anchor='w')
		self.tree.heading('block_time', text='Block Time', anchor='w')

		self.tree.column('date', width=100)
		self.tree.column('aircraft', width=140)
		self.tree.column('callsign', width=90)
		self.tree.column('departure', width=70)
		self.tree.column('arrival', width=70)
		self.tree.column('distance', width=90)
		self.tree.column('block_time', width=90)

		self.tree.pack(pady=10)

		# BUTTONS
		tk.Button(
			self.logbook_tab,
			text='Delete Selected',
			cursor='hand2',
			command=self.delete_selected
		).pack()

		tk.Button(
			self.logbook_tab,
			text='Back',
			cursor='hand2',
			command=lambda: controller.show_frame('HomePage')
		).pack(pady=10)

		# STATS
		self.l_total_flights = tk.StringVar(value='Total Flights: ')
		self.l_total_distance = tk.StringVar(value='Total Distance Flown: NM')
		self.l_total_time = tk.StringVar(value='Total Est. Flight Time:  h m')
		self.l_average_flight_length = tk.StringVar(value='Average Flight Length: NM')
		tk.Label(self.stats_tab, textvariable=self.l_total_flights, font=('Arial', 14)).pack(pady=20)
		tk.Label(self.stats_tab, textvariable=self.l_total_distance, font=('Arial', 14)).pack(pady=20)
		tk.Label(self.stats_tab, textvariable=self.l_total_time, font=('Arial', 14)).pack(pady=20)
		tk.Label(self.stats_tab, textvariable=self.l_average_flight_length, font=('Arial', 14)).pack(pady=20)

		tk.Button(self.stats_tab, text='Back', cursor='hand2', command=lambda: controller.show_frame('HomePage')).pack(pady=10, anchor='s', ipadx=10)

	def load(self, controller):
		self.log = get_flight_log()
		self.flight_stats = self.compute_stats(self.log)

		# update stats
		self.l_total_flights.set(f"Total Flights: {self.flight_stats['total_flights']}")
		self.l_total_distance.set(f"Total Distance Flown: {round(self.flight_stats['total_distance'], 2)} NM")
		self.l_total_time.set(f"Total Est. Flight Time: {self.flight_stats['total_time']}")
		self.l_average_flight_length.set(f"Average Flight Length: {round(self.flight_stats['average_flight_length'], 2)} NM")

		self.dep_combo['values'] = [
			'All',
			*sorted({x['departure'] for x in self.log})
		]

		self.arr_combo['values'] = [
			'All',
			*sorted({x['arrival'] for x in self.log})
		]

		self.aircraft_combo['values'] = [
			'All',
			*sorted({x['aircraft_icao'] for x in self.log})
		]

		self.airline_combo['values'] = [
			'All',
			*sorted({x['callsign'][:3] for x in self.log})
		]

		self.refresh_tree(self.log)

	def compute_stats(self, flight_log):
		def parse_block_time(block_time):
			hours = 0
			minutes = 0

			h = re.search(r'(\d+)h', block_time)
			m = re.search(r'(\d+)m', block_time)

			if h:
				hours = int(h.group(1))
			if m:
				minutes = int(m.group(1))

			total_minutes = hours * 60 + minutes

			return total_minutes

		total_flights = len(flight_log)
		total_distance = 0
		total_time_minutes = 0

		for flight in flight_log:
			total_distance += flight.get('distance', 0)
			total_time_minutes += parse_block_time(flight.get('block_time', '0m'))

		total_time = f'{total_time_minutes // 60}h {total_time_minutes % 60}m'

		avg_flight_length = (
			total_distance / total_flights if total_flights > 0 else 0
		)

		return {
			'total_flights': total_flights,
			'total_distance': total_distance,
			'total_time': total_time,
			'average_flight_length': avg_flight_length
		}

	def refresh_tree(self, flights):
		for row in self.tree.get_children():
			self.tree.delete(row)

		for i, flight in enumerate(flights):
			self.tree.insert(
				"",
				tk.END,
				iid=i,
				values=(
					flight['date'],
					flight['aircraft'],
					flight['callsign'],
					flight['departure'],
					flight['arrival'],
					f"{flight['distance']} NM",
					flight['block_time']
				)
			)

	def apply_filters(self):
		filtered = []

		for flight in self.log:
			if self.dep_filter.get() != "All":
				if flight['departure'] != self.dep_filter.get():
					continue

			if self.arr_filter.get() != "All":
				if flight['arrival'] != self.arr_filter.get():
					continue

			if self.aircraft_filter.get() != "All":
				if flight['aircraft_icao'] != self.aircraft_filter.get():
					continue

			if self.airline_filter.get() != "All":
				if flight['callsign'][:3] != self.airline_filter.get():
					continue

			filtered.append(flight)

		self.refresh_tree(filtered)

	def clear_filters(self):
		self.dep_filter.set('All')
		self.arr_filter.set('All')
		self.aircraft_filter.set('All')
		self.airline_filter.set('All')

		self.refresh_tree(self.log)

	def delete_selected(self):
		selected = self.tree.selection()

		if not selected:
			return

		index = int(selected[0])

		if not messagebox.askyesno(
			'Delete Flight',
			'Delete selected flight?'
		):
			return

		delete_flight(index)
		self.load(None)