#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# @author Paul Petring

from pprint import pprint
from lxml import etree
import hashlib
import requests
import json
from lxml import html

import datetime
from datetime import datetime, timedelta
import pytz

class FritzBox:
	"""
		allows to interact with Fritzbox OS 6.30 - 6.60 by using HTTP requests
	"""

	_url="" #URL of the FritzBox
	_username="" #username of the FritzBox
	_password="" #password of the FritzBox
	_sid="" #current session identifier 
	_last_calls=[] #calls buffer 
	_last_phonebook_entries=[] #devices buffer
	_last_devices=[] #devices buffer
	_request_session = requests.Session() #request session object 
	_request_headers = { #default headers, feel free to modify these
		'Referer': 'http://fritz.box/',
		'Pragma' : 'no-cache',
	    'User-Agent': 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36',
	    'Accept-Language': 'en-US,en;q=0.8,de;q=0.6',
	    'Accept-Encoding': 'gzip, deflate, sdch',
	    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
	    'Connection': 'keep-alive',
	    'Cache-Control': 'no-cache',
	    }



	def __init__(self,password="",url="http://fritz.box",username="",login=True):
		"""
			@param password of your fritz.box (no username support yet)
			@param url of your fritzbox (defaults to "http://fritz.box") 
		"""
		self._url = url
		self._password = password
		self._username = username
		if(login):
			self._sid = self.login()
		if(self._url!="http://fritz.box"):
			self._request_headers["Referer"] = self._url + "/"

	def getSID(self):
		""" returnes current SID status and challenge 
			required for logging into the FritzBox			
		"""
		status_url = self._url + "/login_sid.lua"
		r = self._request_session.get(status_url) 

		"""Expected response:
			<?xml version="1.0" encoding="utf-8"?>
			<SessionInfo>
				<SID>0000000000000000</SID>
				<Challenge>443a0e07</Challenge>
				<BlockTime>0</BlockTime>
				<Rights></Rights>
			</SessionInfo>
		"""

		#Parsing XML
		parser = etree.XMLParser(recover=True)
		root = etree.fromstring(str(r.content), parser=parser)
		ret_sid=root.find('SID').text
		challenge=root.find('Challenge').text
		return (ret_sid,challenge)

	def login(self):
		"""
			performs an login by getting the FirtzBox session challenge
			hashing it in combination with the provided password and
			returning the newly achieved session identifier
		"""

		sid_status = self.getSID()
		self._sid = sid_status[0]
		challenge = sid_status[1]

		if(sid_status[0]=="0000000000000000"): # login procedure required
			
			#following the login javascript of OS 6.30+
			#encoding it to utf-16E does the trick to get the correct hash
			cp_str = challenge + "-" + self._password 
			md5_str = hashlib.md5(cp_str.encode("utf-16LE")).hexdigest()
			response = challenge + "-" + md5_str
			
			#preparing POST statement 
			post = "response="+response+"&lp=&username="+self._username
			data = dict(response=response, lp='',username=self._username)
			r = self._request_session.post(self._url, data=data, allow_redirects=True,headers=self._request_headers)
			
			#extracting SID from response (mostly in the last few lines of response)
			self._sid = r.content[r.content.find('"sid":'):]
			self._sid = self._sid[8:self._sid.find("});")-2]
		return self._sid;

	def get_devices(self,device_type="active"):
		"""
			returns a list of the current home network devices as FritzBoxDevice objects
			@device_type defaults to active devices, else returns inactive (passive) devices of home network
		"""
		data = dict(xhr=1, sid=self._sid, lang='en',page='netDev',type="cleanup")
		r = self._request_session.post(self._url+"/data.lua", data=data, allow_redirects=True,headers=self._request_headers)
		#r.content should contain valid json string with active and passive devices
		parsed=json.loads(r.content)
		
		ret_list=[]
		if(device_type=="active"):
			for active in parsed["data"]["active"]:
				ret_list.append(FritzBoxDevice(active))
		else:
			for passive in parsed["data"]["passive"]:
				ret_list.append(FritzBoxDevice(passive))
		return ret_list

	def get_foncalls(self):
		"""
			returns a list of last 400(?) fon calls as FritzBoxCall objects
		"""
		data = dict(sid=self._sid)
		r = self._request_session.post(self._url+"/fon_num/foncalls_list.lua?sid="+self._sid+"&csv=", data=data, allow_redirects=True,headers=self._request_headers)
		#r.content contains semicolon separated values, surrounding head and tail line
		ret_list = []
		for line in r.content.split('\n')[2:-1]:
			ret_list.append(FritzBoxCall(line))
		_last_calls = ret_list
		return ret_list

	def get_fonbook(self):
		
		""" #downloading it from the button ended in timeout	
		data = dict(sid=self._sid,PhonebookId=0,PhonebookExportName="Telefonbuch",PhonebookExport="")
		print data		
		r = self._request_session.post(self._url+"/cgi-bin/firmwarecfg", data=data, allow_redirects=True,headers=self._request_headers)
		print(r.content)	
		"""

		# as a workaround we parse the delivered table
		data = dict(sid=self._sid,xhr=1,page="bookLi",no_sidrenew="",lang="en")
		r = self._request_session.post(self._url+"/data.lua", data=data, allow_redirects=True,headers=self._request_headers)
		tree = html.fromstring(r.content.decode('utf-8'))
		tree_names = tree.xpath('//table[@id="uiInnerTable"]/tr')
		
		ret_list = []
		for name_row in tree_names[:-1]: #removing the "no entries-entry
			entry = FritzBoxFonBookEntry( )
			entry.name = ''.join(name_row.xpath('td[@class="tname"]/text()')).encode('utf-8')
			entry.numbers = name_row.xpath('td[@class="tnum"]/text()') #string list!
			entry.type = ''.join(name_row.xpath('td[@class="ttype"]/text()')).encode('utf-8')
			entry.code = ''.join(name_row.xpath('td[@class="tcode"]/text()')).encode('utf-8') 
			entry.vanity = ''.join(name_row.xpath('td[@class="tvanity"]/text()')).encode('utf-8') 
			entry.imp = ''.join(name_row.xpath('td[@class="timp"]/text()')).encode('utf-8')
			ret_list.append(entry)
		self._last_phonebook_entries = ret_list 
		return ret_list

class FritzBoxFonBookEntry:
	name = ""
	numbers = []
	type  = ""
	vanity = ""
	code  = ""
	imp = ""

	def __init__(self, name="", numbers="",type="",code="",vanity="",imp=""):
		self.name=name
		self.numbers=numbers
		self.type=type
		self.code=code
		self.vanity=vanity
		self.imp=imp

	def __repr__(self): #debug purposes
		return str(self.name) #+ " " +''.join(str(e) for e in self.numbers)
	def __str__(self): #debug purposes
		return str(self.name) #+ " " +''.join(str(e) for e in self.numbers)

class FritzBoxCall:
	call_type="" #int
	date="" #dateTime
	caller_name="" #name of the caller set by FritzBox fon book
	caller_number="" #number of the caller as string, as it can be anonymous
	fon="" #name of the called internal device
	number="" #number of the called internal devices
	duration="" #duration as python timespan
	UID="" #unique identifier of the call

	def __init__(self,csv_line):
		parts=csv_line.split(';')
		self.call_type = int(parts[0])
		parse_date = datetime.now(pytz.timezone('Europe/Berlin'))
		tz = pytz.timezone('Europe/Berlin')
		self.date =  parse_date.strptime(parts[1] + " CET", "%d.%m.%y %H:%M %Z")
		tzoffset = tz.utcoffset(self.date)
		self.date = self.date-tzoffset

		self.caller_name = parts[2]
		self.caller_number = parts[3]
		self.fon = parts[4]
		self.number = parts[5] 
		t = datetime.strptime(parts[6],"%H:%M")
		self.duration = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
		self.UID = self.get_UID()
	
	def get_UID(self):
		return hashlib.md5(self.date.isoformat()+self.caller_number).hexdigest()

	def __repr__(self): #debug purposes
		return str(self.date) + " " +self.caller_name + " " +self.caller_number + " " +str(self.duration)

	def __str__(self): #debug purposes
		return str(self.date) + " " +self.caller_name + " " +self.caller_number + " " +str(self.duration)


class FritzBoxDevice:
	mac="" #mac adress as string
	ipv6="" #ipv6 adress of the device as string
	state="" # state as string
	name="" # name as string
	port="" # port as string
	summarypropertie="" # summarypropertie as string (no typo! missing r is real)
	classes="" # classes as string
	url="" # url as string 
	type="" # type as string (lan|wlan etc)
	ipv4="" # ipv4 as string
	UID="" #UID as string

	def __init__(self,parsed_json):
		"""
			expected parsed json and inits values as string
		"""
		self.mac=parsed_json["mac"]
		self.ipv6=parsed_json["ipv6"]
		self.UID=parsed_json["UID"]
		self.state=parsed_json["state"] 
		self.port=parsed_json["port"]
		self.name=parsed_json["name"]
		self.summarypropertie=parsed_json["summarypropertie"]
		self.classes=parsed_json["classes"]
		self.url=parsed_json["url"]
		self.type=parsed_json["type"]
		self.ipv4=parsed_json["ipv4"]
		self.UID=self.get_UID()


	def get_UID(self):
		if self.UID:
			return self.UID
		return str(self) #if vpn UID seems to be empty
		

	def __repr__(self): #debug purposes
		return self.UID + " " +self.ipv4 + " " +self.type + " " +self.name

	def __str__(self): #debug purposes
		return self.UID + " " +self.ipv4 + " " +self.type + " " +self.name

