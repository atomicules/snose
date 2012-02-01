#!/usr/bin/python
#snose - 

import simplejson as json
from simplenote import Simplenote #Need to install this
import os.path, time
from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.add_option("--snort", action="store", type="string", help="Import a new file to Simplenote")
	parser.add_option("--sniff", action="store", nargs=2, type="string", help="Link a file with an already existing note in  Simplenote", metavar="<key> <filename>")
	parser.add_option("--sneeze", action="store", nargs=2, type="string", help="Export an existing file from Simplenote", metavar="<key> <filename>")
	parser.add_option("--sync", help="Sync files in index", default=False, action='store_true')
	parser.add_option("--hanky", help="Use with --sync to perform a dry run", default=False, action='store_true')
	parser.add_option("--snot", help="List notes available for export (tagged snose)", default=False, action='store_true')
	parser.add_option("--username", action="store", type="string", help="Your Simplenote email address")
	parser.add_option("--password", action="store", type="string", help="Your Simplenote password")
	(options, args) = parser.parse_args()

	if not options.username or not options.password:
		#Check to see if stored somewhere
		try:
			with open(os.path.join(os.path.expanduser('~'), '.snoseauth'), 'r') as f:
				auth = json.load(f)
			options.username = auth['username']
			options.password = auth['password']
		except IOError as e:
			print 'Username and password must be supplied or exist in json form in a file called .snoseauth in your home directory'
			exit()
	snclient = Simplenote(options.username, options.password)
	if options.snort:
		snort(snclient, options.snort)
	elif options.sniff:
		sniff(snclient, options.sniff[0], options.sniff[1])
	elif options.sneeze:
		sneeze(snclient, options.sneeze[0], options.sneeze[1])
	elif options.snot:
		snot(snclient)
	elif options.sync and options.hanky:
		sync(snclient, True)
	elif options.sync:
		sync(snclient)
	else:
		print 'No options supplied'

		


def snort(snclient,filename): 
	# Add a new mapping, is actually add a new file
	try: #http://stackoverflow.com/questions/82831/how-do-i-check-if-a-file-exists-using-python#85237
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		#Doesn't exist so create new
		snose = {}
	#Add new file to Simplenote
	#Need to get file contents
	try:
		with open(filename, 'r') as f:
			content = f.read()
		returned = snclient.add_note({"content": content, "tags": ["snose"]})
		#Add mapping
		snose[filename] = {'key': returned[0]['key'], 'syncnum': returned[0]['syncnum'], 'version': returned[0]['version'], 'modifydate': returned[0]['modifydate'] }
		#Write back out
		with open('.snose', 'w') as f:
			json.dump(snose, f, indent=2)
	except IOError as e:
		pass

def sniff(snclient,key, filename): #How to ensure remote gets or has snose tag?
	# Add a new mapping only
	try: #http://stackoverflow.com/questions/82831/how-do-i-check-if-a-file-exists-using-python#85237
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		#Doesn't exist so create new
		snose = {}
	#Get details about current Simplenote file
	remote = snclient.get_note(key)
	#What if can't be found, need to abort...
	try:
		#Add mapping
		snose[filename] = {'key': remote[0]['key'], 'syncnum': remote[0]['syncnum'], 'version': remote[0]['version'], 'modifydate': remote[0]['modifydate'] }
		#Write back out
		with open('.snose', 'w') as f:
			json.dump(snose, f, indent=2)
	except IOError as e:
		pass

def sneeze(snclient, key, filename):
	#place an existing note in current directory
	#Need some UI for getting list of keys
	#Get remote note
	remote = snclient.get_note(key)
	#Add mapping
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		#Doesn't exist so create new
		snose = {}
	remote = snclient.get_note(key)	
	try:
		snose[filename] = {'key': remote[0]['key'], 'syncnum': remote[0]['syncnum'], 'version': remote[0]['version'], 'modifydate': remote[0]['modifydate'] }
		#Write back out
		with open('.snose', 'w') as f:
			json.dump(snose, f, indent=2)
	except IOError as e:
		pass
	#Write file itself
	try: 
		with open(filename, 'w') as f:
			f.write(remote[0]['content'])
	except IOError as e:
			pass
	#Now then, only problem with this is that if sync is called, this will be "modified" and will get synced unnecessarily
	#Not sure how to get around this? Override the local['modifydate']?? I think so...
	#but then need to do that after file has written to disk

def snot(snclient):
	#List simplenote notes
	notelist = snclient.get_note_list()
	#That gets list of keys. Then need to iterate through and get first line of text.
	#This is going to be slow. Perhaps limit to a tag is a good idea
	print "Key:                                    Note"
	for note in notelist[0]:
		if "snose" in note['tags']:
			#get note itself
			remote = snclient.get_note(note['key'])
			print remote[0]['key']  + "  " + remote[0]['content'].splitlines()[0]


def sync(snclient, dry=False):
	#Need to read in mappings and sync those notes.
	success = False
	dryremotes = []
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		print 'Error reading Index file'
		exit()
	#Need to iterate through list.
	for name, local in snose.iteritems():
		#First of all check for local modifications
		if float(os.path.getmtime(name)) > float(local['modifydate']): #ensure full timestamp
			if not dry:
				#Update remote
				with open(name, 'r') as f:
					content = f.read()
				returned = snclient.update_note({'key': local['key'], 'content': content })
				#Update Index
				snose[name]['syncnum'] = returned[0]['syncnum']
				snose[name]['version'] = returned[0]['version']
				snose[name]['modifydate'] = returned[0]['modifydate']
				try:
					with open('.snose', 'w') as f:
						json.dump(snose, f, indent=2)
					success = True
				except IOError as e:
					print 'Failed to update index'
				#Give some feedback?
			if dry or success:
				print "Updated remote version of "+ name
				#For dry run, collect list of "updated remotes" to ignore in local updates
				if dry: dryremotes.append(name)
		#Fetch details from Simplenote
		remote = snclient.get_note(local['key'])
		if remote[0]['syncnum'] > local['syncnum']:
			if not dry:
				#update local file contents
				try: 
					with open(name, 'w') as f:
						f.write(remote[0]['content'])
					#Also update .snose index
					snose[name]['syncnum'] = remote[0]['syncnum']
					snose[name]['version'] = remote[0]['version']
					snose[name]['modifydate'] = os.path.getmtime(name) #As if set remote modify date, local file will immediately appear 'modified'
					try:
						with open('.snose', 'w') as f:
							json.dump(snose, f, indent=2)
						success = True
					except IOError as e:
						print 'Failed to update index'
					#Some feedback
				except IOError as e:
					pass
			if (dry and (not (name in dryremotes))) or success:
				print "Updated local version of "+ name


main()
