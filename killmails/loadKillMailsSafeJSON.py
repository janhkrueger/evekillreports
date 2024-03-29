#!/usr/bin/env python2.7
# encoding: utf-8

import sys, gzip, StringIO, sys, math, os, getopt, time, json, socket
import urllib2
import MySQLdb
import ConfigParser
import codecs
import time
import StringIO
from datetime import datetime
from elementtree.ElementTree import parse
from pprint import pprint
import xml.etree.ElementTree as ET
import requests


conf = ConfigParser.ConfigParser()
conf.read(["/var/games/KillReporter/init.ini", "init_local.ini"])

cursor = None
db = None

def db_init():
	db_schema = conf.get("GLOBALS","db_name")
	db_IP = conf.get("GLOBALS","db_host")
	db_user = conf.get("GLOBALS","db_user")
	db_pw = conf.get("GLOBALS","db_pw")
	db_port = int(conf.get("GLOBALS","db_port"))

	global cursor,db
	db = MySQLdb.connect(host=db_IP, user=db_user, passwd=db_pw, port=db_port, db=db_schema)
	cursor = db.cursor()

def getData(url):
	request_headers = {
		"Accept":"application/json",
		"Accept-Encoding":conf.get("GLOBALS","loadencoding"),
		"Maintainer":"Achanjati",
		"Mail":conf.get("GLOBALS","mail"),
		"Twitter":"@janhkrueger",
		"User-Agent":"RASI loadKillMails - Init"
	}

	try:
		request = urllib2.Request(url, headers=request_headers)
        	opener = urllib2.build_opener()
        	raw_zip = opener.open(request)
        	dump_zip_stream = raw_zip.read()
        	dump_IOstream = StringIO.StringIO(dump_zip_stream)
        	zipper = gzip.GzipFile(fileobj=dump_IOstream)
		data = json.load(zipper)
	except urllib2.HTTPError:
		return "HTTP ERROR"
	except httplib.HTTPException:
		return "HTTP Exception"
	return data

def main():
	db_init()
	conf = ConfigParser.ConfigParser()
	conf.read(["/var/games/KillReporter/init.ini", "init_local.ini"])

	jetzt =  str(datetime.now())

	sql = "SELECT * FROM KR_participantsHash WHERE collected = 0 AND crestHash IS NOT NULL ORDER BY killID DESC LIMIT 0,1000;"
	cursor.execute( sql)
	
        killmailurl = conf.get("LOADKILLMAIL","killmail")

	rows = cursor.fetchall()
	lastKillID=0
        for kill in rows:
		# fehler = 99	
		killid = kill[0]
		#print killid
		cresthash = kill[1]

		# Zusammenbauen der URL der KillMail
		killmailurldetail = killmailurl % (killid, cresthash)
		# Abfragen des Krieges
		try:
			data = getData(killmailurldetail)
			fehler = 0
			if data == "HTTP ERROR":
				raise ValueError('A very specific bad thing happened')
		except IOError:
			#print " >>> IOError bei KillMail %s, beende Verarbeitung." % killid
			sql = "UPDATE KR_participantsHash SET collected = 8 WHERE killID={0} AND crestHash='{1}'".format(killid, cresthash)
                	cursor.execute(sql)
                	db.commit()
			fehler = 8
			#sys.exit(8)
		except ValueError as err:
			fehler = 3
			# print " >>> Hash moeglicherweise falsch?  %s" % killid
			# 3 = konnte killMail nicht vom Server laden
			sql = "UPDATE KR_participantsHash SET collected = 3 WHERE killID={0}".format(killid)
                	cursor.execute(sql)
                	db.commit()
			#sys.exit(3)
		except:
        		# print " >>> Fehler beim Lesen der KillMail %s" % killid
			sql = "UPDATE KR_participantsHash SET collected = 4 WHERE killID={0} AND crestHash='{1}'".format(killid, cresthash)
                	cursor.execute(sql)
                	db.commit()
			fehler = 4
			#sys.exit(4)

		# print killid, lastKillID
        	#parsed   = json.loads(data,encoding='utf-8')
        	# Hier jetzt in eine Datei umleiten
		#print (data)
        	filename = 'killjson/%s.json' % killid
        	with open( filename, 'w' ) as outfile:
           		json.dump(data, outfile)
           		#outfile.write(data)
			# print killid
			sql = "UPDATE KR_participantsHash SET collected = 15 WHERE killID={0} AND crestHash='{1}'".format(killid, cresthash)
			cursor.execute(sql)
			db.commit()
		fehler = 99

	cursor.close()
	db.close()


if __name__ == "__main__":
	main()
