#!/usr/bin/env python
# -*- coding: utf-8 -*- 
from FritzBox import FritzBox
from GoogleCalendarWrapper import GoogleCalendarWrapper
from pprint import pprint

import datetime
from datetime import datetime, timedelta
from dateutil import parser
import pytz

def handleFonEntriesToGoogleCalendar(calendar,events,calls):
	""" Takes a list of FritzBoxCalls and adds them to the provided Calender object.
	 	Unique IDs are used to prevent multiple entries for a call.	
	"""
	for call in calls:
		print call
		event={ 'summary': call.caller_number + " " + call.caller_name,
					'location': 'Dresden, Saxony, Germany',
					'description': call.UID,
					'start': {
							'dateTime': str(call.date.isoformat() + 'Z'),
							'timeZone': 'Europe/Berlin',
							},
					'end': {
							#'dateTime': str((pytz.utc.localize(call.date).astimezone(pytz.utc)+call.duration).isoformat()[:-6] + 'Z'),
							'dateTime': str((call.date+call.duration).isoformat() + 'Z'),
							'timeZone': 'Europe/Berlin',
						  },
				}
		found=False

		for item in events:
			if item["UID"] == call.UID:
				found = True
		if (found==False):
			#print "new phone call found:"
			#pprint(event)
			calendar.create_event(event)
	return

def handleDeviceEntriesToGoogleCalendar(calendar,events,devices):
	""" Takes a list of FritzBoxDevices and adds them to the provided Calender object.
	 	Unique IDs are used to extend existing events and create nw ones accordingly.	
	"""
	for device in devices:
		#print device
		event={ 'summary': device.name + " " + device.ipv4 + " " + device.type,
					'location': 'Dresden, Saxony, Germany',
					'description': device.UID,
					'start': {
							'dateTime': str(datetime.utcnow().isoformat() + 'Z'),
							'timeZone': 'Europe/Berlin',
							},
					'end': {
							'dateTime': str((datetime.utcnow()+ timedelta(minutes=5)).isoformat() + 'Z'),
							'timeZone': 'Europe/Berlin',
						  },
				}
		#print event

		found=False

		for item in events:
			
			if item["UID"] == device.UID:
				found = True
				try:
					parsed_time = parser.parse(item["end"]["dateTime"]).astimezone(pytz.utc);
					#in case the given device has an ending time in the future, we'll extend that event
					#else it gets an new event created
					if parsed_time >= pytz.utc.localize(datetime.utcnow()) : #wierd to localize utcnow to utc
						#handle if event is currently active
						calendar.update_event({'id' : item['id'] , 'end': {
									'dateTime': str((datetime.utcnow()+ timedelta(minutes=5)).isoformat() + 'Z'),
									'timeZone': 'Europe/Berlin',
								}})
					else: #we will create the thing again as a new event
						found=False #not necessary but easier to read
				except Exception,e:
					print "error while handling"
					print e
					pprint(item)
					pass #more stable

		if (found==False):
			#print "new device state"
			#pprint(event)
			calendar.create_event(event)
	return


def main():

	box = FritzBox("YOUR_PASSWORD")	
	fon_calendar = GoogleCalendarWrapper("YOUR_CALENDAR_ID@group.calendar.google.com");
	devices_calendar = GoogleCalendarWrapper("YOUR_CALENDAR_ID@group.calendar.google.com")
	

	print "Getting fon_calendar Events"
	fon_events = fon_calendar.get_events()
	print "Found " + str(len(fon_events)) + " existing fon_events."

	print "Getting device_calendar Events"
	device_events = devices_calendar.get_events()
	print "Found " + str(len(device_events)) + " existing device_events."
	
	print "Getting active devices:"
	active_devices = box.get_devices("active")
	print "Found " + str(len(active_devices)) + " active devices."

	print "Getting passive devices:"
	passive_devices = box.get_devices("passive")
	print "Found " + str(len(passive_devices)) + " passive devices."

	print "Getting recent phone calls:"
	recent_calls=box.get_foncalls()
	print "Found " + str(len(recent_calls)) + " existing recent_calls."

	handleFonEntriesToGoogleCalendar(fon_calendar,fon_events,recent_calls)
	handleDeviceEntriesToGoogleCalendar(devices_calendar,device_events,active_devices)

	print "done"
	return

if __name__ == '__main__':
	main()