*Made by Ben Collingridge*

## Pre-requisites

### How to create .exe file
1. First, install PyInstaller [PyInstaller - PyPI](https://pypi.org/project/pyinstaller/)

`py -m pip install pyinstaller`

2. Next, run PyInstaller:

`py -m PyInstaller --noconsole --onefile --name "Flight Generator" --icon "assets/app_icon.ico" --add-data "assets/app_icon.ico;assets" main.py`

*If you cannot create an .exe file, you can just run main.py or rename main.py to main.pyw for no console.*

## Getting started with Flight Generator
### Config files
- Create a config file by clicking 'new' at the top of the home page.
- You can add items to the lists by typing directly below them and clicking 'add item' or pressing enter on your keyboard.
- This will then be automatically selected. You change the config file at any point by clicking 'select' at the top of the home page.
- If you need to edit the selected config file, you can do so by clicking 'edit'.
- If you are creating or editing a config file, you can double click an item to edit it.
- You can also delete items by selecting them and then clicking 'remove selected'.

### Creating a flight
- Once you have a valid config file selected, you can press 'get flight' to generate a random flight based on your parameters.
- At this point, the button will turn blue. Please do not click it again.
- Once the data has been returned and printed on the screen, you will have cooldown (seen at the top of the screen) which you will have to wait for before generating a new flight.
- Once you are happy with one of the generated flights, you can click 'fly now' at the bottom of the screen to add it to your flight log.

### Viewing your flight log
- You can view your flight at any time by clicking the button at the bottom of the home page.
- From here, you will see all your logged flights.
- You can use the filters at the top of the window and then press 'apply' to see the changes.
- You can also click 'reset' to remove the filters at any point.
- If you would like to remove a flight from your flight log, you can select it and then click 'remove selected' at the bottom of the window.

## Other info
- Flight data is retrieved using `pyflightdata` which can be found here: [pyflightdata - PyPI](https://pypi.org/project/pyflightdata/)
- As many live/near future flights are selected as possible, but to reach the defined limit, the available flights may be back-filled with past flights where necessary.
- All callsigns, routes, aircraft, and other feature data are real.