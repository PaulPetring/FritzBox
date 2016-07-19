#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author Paul Petring

import sys
import imaplib
import getpass
import email
import email.header
import datetime
from datetime import datetime, timedelta
import time
from pprint import pprint

import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

class GoogleCalendarWrapper:
	_calendarID = ""
	SCOPES = 'https://www.googleapis.com/auth/calendar' #' # do not use .readonly' and reset the key in case you already did
	CLIENT_SECRET_FILE = './client_secret.json'
	APPLICATION_NAME = 'Google Calendar API Python Quickstart'
	credentials = ""
	http = ""
	service = ""


	def __init__(self,calendarID):
		self._calendarID = calendarID
		self.credentials = self.get_credentials()
		self.http = self.credentials.authorize(httplib2.Http())
		self.service = discovery.build('calendar', 'v3', http=self.http)

	def get_credentials(self): 
		"""Gets valid user credentials from storage.

		If nothing has been stored, or if the stored credentials are invalid,
		the OAuth2 flow is completed to obtain the new credentials.

		Returns:
			Credentials, the obtained credential.
		"""
		current_dir = os.path.expanduser('.')
		credential_path = os.path.join(current_dir, 'calendar.json')

		store = oauth2client.file.Storage(credential_path)
		credentials = store.get()
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
			flow.user_agent = APPLICATION_NAME
			if flags:
				credentials = tools.run_flow(flow, store, flags)
			else: # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
			print('Storing credentials to ' + credential_path)
		return credentials

	def get_events(self,days=365,maxResults=10000):
		""" 
			gets recent calendar entries from calendar
		"""
		now = (datetime.utcnow() - timedelta(days=days)).isoformat() + 'Z'

		eventsResult = self.service.events().list(
			calendarId=self._calendarID, timeMin=now, maxResults=maxResults, singleEvents=True,
			orderBy='startTime').execute()
		ret_list = eventsResult.get('items', []) 
		for item in ret_list:
			#writing the current UID to the description field to identify the event later on
			#might be improved to search for an UID line like UID: identifer to be able to use
			#the description for other purposes too
			if "description" in item.keys():
				item["UID"] = item["description"] #adding UID due to missing CustomCalendarClass
			else:
				pprint(item)
		return ret_list

	def provide_empty_event():
		return { 'summary': '',
						'location': '',
						'description': '',
						'start': {
								'dateTime': datetime.utcnow().isoformat() + 'Z',
								'timeZone': 'Europe/Berlin',
								},
						'end': {
								'dateTime': (datetime.utcnow() + timedelta(minutes=2)).isoformat() + 'Z',
								'timeZone': 'Europe/Berlin',
							  },
						'recurrence': [ 
										'' #'RRULE:FREQ=DAILY;COUNT=2'
               		             	],
               'attendees': [
                             # {'email': 'mail@example.com'},
                            ],
               'reminders': {
                             #'useDefault': False,
                             #'overrides': [
                             #              {'method': 'email', 'minutes': 24 * 60},
                             #              {'method': 'popup', 'minutes': 10},
                             #             ],
                            }
				}

	def create_event(self,event):
		event = self.service.events().insert(calendarId=self._calendarID, body=event).execute()
		return

	def update_event(self,event_to_be_handled):	
		
		try:
			# etrieve the existing event from the API.
			event = self.service.events().get(calendarId=self._calendarID, eventId=event_to_be_handled["id"]).execute()
			
			#only updating provided elements
			for key in event_to_be_handled.keys():
				event[key] = event_to_be_handled[key]
			
			#trigger update
			updated_event = self.service.events().update(calendarId=self._calendarID, eventId=event_to_be_handled["id"], body=event).execute()

		except Exception,e: 
			print "error while updating"
			print e
			print event_to_be_handled
			print event
			pass

		return






