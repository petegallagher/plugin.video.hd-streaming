import os
import sys
import csv
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import urllib
import urllib2
import cookielib
import mechanize
from bs4 import BeautifulSoup
import json

MODE_SCHEDULE = 10
MODE_LIVE_STREAMS = 20
MODE_PLAY   = 30 
MODE_UPCOMING = 40
PARAMETER_KEY_MODE = "mode"
SCHEDULE = "Streams today"
UPCOMING = "Upcoming Streams for the next days"
LIVE_STREAMS = "Live Streams"
VERSION = xbmc.getInfoLabel("System.BuildVersion").replace(" Git:",".") + "-" + xbmc.getInfoLabel("ListItem.Property(Addon.Version)")
schedule_path  = os.path.join(xbmc.translatePath('special://profile/addon_data'), 'plugin.video.hd-streaming.schedule.txt')
channels_path  = os.path.join(xbmc.translatePath('special://profile/addon_data'), 'plugin.video.hd-streaming.channels.txt')
upcoming_path  = os.path.join(xbmc.translatePath('special://profile/addon_data'), 'plugin.video.hd-streaming.upcoming.txt')
settings    = xbmcaddon.Addon("plugin.video.hd-streaming");
handle = int(sys.argv[1])
SETTINGS_URL = settings.getSetting("settings_url")

def parameters_string_to_dict(parameters):    
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def login():
	channels_list=[]
	date_list=[]
	teams_list=[]
	channels_bar_list=[]
	schedule = []
	username = settings.getSetting("username")
	password = settings.getSetting("password")
	url = 'http://hd-streaming.tv/api/?request=login'
	url2 = 'http://hd-streaming.tv/watch/livehds'
	url3 = 'http://hd-streaming.tv/watch/upcoming-matches'
	req = mechanize.Browser()
	req.addheaders = [('User-agent','Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0')]
	req.addheaders = [('Referer','http://news-source.tv/')]
	req.set_handle_robots(False)
	req.set_handle_redirect(True)
	values = {'platform':'XBMC','version':VERSION,'username':username,'password':password}
	logindata = urllib.urlencode(values)
	loginreq = urllib2.Request(url, logindata)
	loginresponse = urllib2.urlopen(loginreq)
	global auth_response
	auth_response = loginresponse.read()
	if "ERROR" in auth_response:
		return False
	response2 = req.open(url2)
	soup = BeautifulSoup(response2.read())
	channels_bar = soup.findAll('a', {"class" : "ch-link"})
	if len(channels_bar) > 0:
		for channel_name in channels_bar:
			channels_bar_list.append(channel_name.string)
		file = open(channels_path,'wb+')
		for i in channels_bar_list:
			file.write(i+"\n")
		file.close()
		file = open(schedule_path,'wb+')
		table_list = soup.findAll('table',{"class" : "views-table"})
		for table in table_list:
			try:
				file.write(table.find('caption').string+"|\n")
			except Exception:
				file.write("|\n")
			channels_list = []
			date_list=[]
			teams_list=[]
			channels = table.findAll('td', {"class" : "views-field-field-eum-channel"})
			date_time = table.findAll('td', {"class" : "views-field-field-eum-datetime-1"})
			teams = table.findAll('td', {"class" : "views-field-field-eum-title"})
			for i in channels:
				channels_list.append(i.find('a').string)
			for i in date_time:
				date_list.append(i.find('span').string)
			for i in teams:
				teams_list.append(i.string.strip())
			for i in range(0,len(channels_list)):
				file.write("   "+channels_list[i].encode('utf-8') + "|" + date_list[i].encode('utf-8') + " " + teams_list[i].encode('utf-8')+"\n")
		file.close()
		upcoming_file = open(upcoming_path,'wb+')
		response3 = req.open(url3)
		upcoming_soup = BeautifulSoup(response3.read())
		days_div = upcoming_soup.findAll('div',{"class" : "view-grouping"})
		for day in days_div:
			days = day.findAll('div',{"class" : "view-grouping-header"})
			for j in days:
				upcoming_days_list=[]
				upcoming_file.write(j.string+"\n")
				upcoming_days_list.append(j.string)
				tables = day.findAll('table',{"class" : "views-table"})
				for table in tables:	
					upcoming_sport_list = []
					upcoming_channels_list = []	
					upcoming_date_list = []
					upcoming_teams_list = []
					upcoming_leagues_list =[]
					upcoming_schedule = []
					upcoming_sport	= table.findAll('caption')
					upcoming_channels = table.findAll('td', {"class" : "views-field-field-eum-channel"})
					upcoming_date_time = table.findAll('td', {"class" : "views-field-field-eum-datetime-1"})
					upcoming_teams = table.findAll('td', {"class" : "views-field-field-eum-title"})
					upcoming_leagues = table.findAll('td', {"class" : "views-field-field-eum-league"})
					for i in upcoming_sport:
						upcoming_sport_list.append(i.string)
					for i in upcoming_channels:
						upcoming_channels_list.append(i.find('a').string)
					for i in upcoming_date_time:
						upcoming_date_list.append(i.find('span',{"class":"date-display-single"}).string)
					for i in upcoming_teams:
						upcoming_teams_list.append(i.string.strip())
					for i in upcoming_leagues:
						upcoming_leagues_list.append(i.string.strip())
					for i in range(0,len(upcoming_channels_list)):
						upcoming_schedule.append(upcoming_channels_list[i]+" "+upcoming_date_list[i]+" "+upcoming_teams_list[i]+" "+upcoming_leagues_list[i])
					for i in range(0,len(upcoming_sport_list)):
						upcoming_file.write("    "+upcoming_sport_list[i]+"\n")
						for j in range(0,len(upcoming_schedule)):
							upcoming_file.write("       "+upcoming_schedule[j].encode('utf-8')+"\n") 
		upcoming_file.close()
		return True
	else:
		return False

def get_schedule():
	matches = []
	data = csv.reader(open(schedule_path, 'rb'), delimiter="|")
	for row in data:
		matches.append(row[0] + " " +row[1])
	return matches

def get_channels():
	# Download the settings JSON file and parse
	f = urllib2.urlopen(SETTINGS_URL)
	settings = json.load(f)

	return settings['channels']

def get_upcoming_schedule():
	upcoming_schedule=[]
	f = open(upcoming_path, 'rb+')
	for line in f:
		upcoming_schedule.append(line)
	return upcoming_schedule

def addDirectoryItem(name, isPlayable=False, isFolder=True, parameters={}):
    li = xbmcgui.ListItem(name)
    if isPlayable==False:
    	li.setProperty('IsPlayable', 'false')
    elif isPlayable==True:
    	li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

def show_root_menu():
	if login():
		addDirectoryItem(name=SCHEDULE, parameters={ PARAMETER_KEY_MODE: MODE_SCHEDULE }, isFolder=True)
		addDirectoryItem(name=UPCOMING, parameters={ PARAMETER_KEY_MODE: MODE_UPCOMING }, isFolder=True)
		addDirectoryItem(name=LIVE_STREAMS, parameters={ PARAMETER_KEY_MODE: MODE_LIVE_STREAMS }, isFolder=True)
		xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
	else:
		if 'password' in auth_response:
			dialog = xbmcgui.Dialog().ok("Login Failed",auth_response)
			settings.openSettings()
		else:
			dialog = xbmcgui.Dialog().ok("Login Failed",auth_response)
    
def show_schedule():
	if len(get_schedule()) == 0:
		addDirectoryItem('No streaming planned for today', isFolder=False)
		xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
	else: 	
		for i in get_schedule():
			addDirectoryItem(i, isFolder=False)
		xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_upcoming_schedule():
	if len(get_upcoming_schedule()) == 0:
		addDirectoryItem('No streaming planned for the next days', isFolder=False)
		xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
	else: 	
		for i in get_upcoming_schedule():
			addDirectoryItem(i, isFolder=False)
		xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_live_streams():
	for channel in get_channels():
		addDirectoryItem(channel['name'], isPlayable=True, isFolder=False, parameters={ PARAMETER_KEY_MODE: MODE_PLAY, 'url':channel['url'],'name':channel['name'] })

	xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_stream(url, name):
	item = xbmcgui.ListItem(path=url)
	item.setInfo('video', {'Title': name})
	return xbmcplugin.setResolvedUrl(handle, True, item)

params = parameters_string_to_dict(sys.argv[2])
mode = int(params.get(PARAMETER_KEY_MODE, "0"))

if not sys.argv[2]:
	username = settings.getSetting("username")
	password = settings.getSetting("password")
	if (len(username) and len(password)) == 0:
		dialog = xbmcgui.Dialog().ok("Username and password are not configured","            You need to input your username and password")
		settings.openSettings()	
	else:
		ok = show_root_menu()
elif mode == MODE_SCHEDULE:
    ok = show_schedule()
elif mode == MODE_UPCOMING:
	ok = show_upcoming_schedule()
elif mode == MODE_LIVE_STREAMS:
    ok = show_live_streams()
elif mode == MODE_PLAY:
	name = urllib.unquote_plus(params["name"])
	url = urllib.unquote_plus(params["url"])
	ok = play_stream(url, name)
