#!/usr/bin/python
#snose - 

import simplejson as json
from simplenote import Simplenote #Need to install this
import os.path, time
from optparse import OptionParser

def main():
	parser = OptionParser()
	parser.add_option("--snort", action="store", type="string", help="Import a new file to Simplenote")
	parser.add_option("--sync", help="Sync files in index", default=False, action='store_true')
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
		returned = snclient.add_note({"content": content})
		#Add mapping
		snose[filename] = {'key': returned[0]['key'], 'syncnum': returned[0]['syncnum'], 'version': returned[0]['version'], 'modifydate': returned[0]['modifydate'] }
		#Write back out
		with open('.snose', 'w') as f:
			json.dump(snose, f, indent=2)
	except IOError as e:
		pass


def sync(snclient):
	#Need to read in mappings and sync those notes.
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
			except IOError as e:
				print 'Failed to update index'')'
			#Give some feedback?
			print "Updated remote version of "+ name
		#Fetch details from Simplenote
		remote = snclient.get_note(local['key'])
		if remote[0]['syncnum'] > local['syncnum']:
			#update local file contents
			try: 
				with open(name, 'w') as f:
					f.write(remote[0]['content'])
				#Also update .snose index
				snose[name]['syncnum'] = remote[0]['syncnum']
				snose[name]['version'] = remote[0]['version']
				snose[name]['modifydate'] = remote[0]['modifydate']
				try:
					with open('.snose', 'w') as f:
						json.dump(snose, f, indent=2)
				except IOError as e:
					print 'Failed to update index'')'
				#Some feedback
				print "Updated local version of "+ name
			except IOError as e:
				pass

def sneeze(key, filename):
	#place an existing note in current directory
	#Need some UI for getting list of keys
	pass

main()
