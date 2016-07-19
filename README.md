#Fritzbox Python for OS 6.30+ (tested up to 6.60)

This project allows to interact with your Fritzbox above the new FritzOS 6.30 to 6.60 (tested with Fritzbox 7490 and 7390). It furthermore uses the Google Calendar API to enter phonecalls and online devices status into your google calendar. 

FritzBox.py works stand alone.

To use the Google Services you will need to generate your own client api credentials including a valid calendar json. For the expected format see the provided default files.

### General Usage FritzBox python class

```
#constructors
box =  FritzBox()
box =  FritzBox("password") # should be default constructor
box =  FritzBox("password", "username")
box =  FritzBox("password", "username", "http://fritz.box")
box =  FritzBox("password", "username", "http://fritz.box",false)

# getting a list of active devices as objects of FritzBoxDevice
devices = box.get_devices(self,"active")

# getting a list of passive devices as objects of FritzBoxDevice
devices = box.get_devices(self,"passive")

# getting a list of objects of FritzBoxCall
calls = box.get_foncalls()
```


### General Usage Google Calendar Wrapper

For phone calls:

```
fon_calendar = GoogleCalendarWrapper("YOUR_CALENDAR_ID@group.calendar.google.com")
fon_events = fon_calendar.get_events()
handleFonEntriesToGoogleCalendar(fon_calendar,fon_events,calls)
```

For active devices tracking:

```
devices_calendar = GoogleCalendarWrapper("YOUR_CALENDAR_ID@group.calendar.google.com")
device_events = devices_calendar.get_events()
handleDeviceEntriesToGoogleCalendar(devices_calendar,device_events,devices)
```

### More

on my website [defendtheplanet.net](defendtheplanet.net)


### TODO 

- add config.json
- implement CalDav Support for non google solutions
- explain vpnc based server setup
- document multiple fritzboxes setup
- add pictures of google calendar entries
- enable gant charts of devices (d3js?)

- get FritzBox phone book(s)
	- sync phone books to Google Contacts
	- sync phone books to CardDav
- get FritzBox system status
	- connection time
- improve Google Calendar UID handling to a single line starting with UID: or something better