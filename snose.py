#!/usr/bin/python
#snose - Simplenote Object Synchronisation (Explicit)

import simplejson as json
from simplenote import Simplenote #Need to install this
import os.path, time
from optparse import OptionParser
import netrc

def main():
	parser = OptionParser()
	parser.add_option("--snort", action="store", type="string", help="Import a new file SNORT to Simplenote")
	parser.add_option("--sniff", action="store", nargs=2, type="string", help="Link a file with an already existing note in  Simplenote", metavar="<key> <filename>")
	parser.add_option("--sneeze", action="store", nargs=2, type="string", help="Export an existing file from Simplenote", metavar="<key> <filename>")
	parser.add_option("--blow", action="store", type="string", help="Roll back note of key BLOW to previous version")
	parser.add_option("--sync", help="Sync files in index", default=False, action='store_true')
	parser.add_option("--hanky", help="Use with --sync to perform a dry run", default=False, action='store_true')
	parser.add_option("--snot", help="List notes available for export (tagged snose)", default=False, action='store_true')
	parser.add_option("--username", action="store", type="string", help="Your Simplenote email address")
	parser.add_option("--password", action="store", type="string", help="Your Simplenote password")
	(options, args) = parser.parse_args()

	if not options.username or not options.password:
		#Check to see if stored somewhere
		try:
			options.username = netrc.netrc().authenticators("simple-note.appspot.com")[0]
			options.password = netrc.netrc().authenticators("simple-note.appspot.com")[2]
		except IOError as e:
			print 'Username and password must be supplied or exist .netrc file under domain of simple-note.appspot.com'
			exit()
	snclient = Simplenote(options.username, options.password)
	if options.snort:
		snort(snclient, options.snort)
	elif options.sniff:
		sniff(snclient, options.sniff[0], options.sniff[1])
	elif options.sneeze:
		sneeze(snclient, options.sneeze[0], options.sneeze[1])
	elif options.blow:
		blow(snclient, options.blow)
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
	except IOError as e:
		print "Failed to read file %s" % filename
	else:
		try:
			returned = snclient.add_note({"content": content, "tags": ["snose"]})
			print "Imported %s into Simplenote with key %s" % (filename, returned[0]['key'])
		except IOError as e:
			print "Failed to add note to Simplenote"
			print e
		else:
			#Add mapping
			snose[filename] = {'key': returned[0]['key'], 'syncnum': returned[0]['syncnum'], 'version': returned[0]['version'], 'modifydate': float(os.path.getmtime(filename)) } #Use actual file mod date
			try:
				#Write back out
				with open('.snose', 'w') as f:
					json.dump(snose, f, indent=2)
			except IOError as e:
				print "Failed to update .snose index file"
				#But note was added to Simplenote so?
				print "But note was successfully imported to Simplenote with key %s. Try sniffing the file" % returned[0]['key']


def sniff(snclient,key, filename): #How to ensure remote gets or has snose tag?
	# Add a new mapping only
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		#Assuming doesn't exist so create new
		snose = {}
	#Get details about current Simplenote file
	try:
		remote = snclient.get_note(key)
		#What if can't be found, need to abort...
	except IOError as e:
		print "Failed to find that note on Simplenote"
		print e
	else:
		try:
			#Add mapping
			snose[filename] = {'key': remote[0]['key'], 'syncnum': remote[0]['syncnum'], 'version': remote[0]['version'], 'modifydate': float(os.path.getmtime(filename)) }
			#Write back out
			with open('.snose', 'w') as f:
				json.dump(snose, f, indent=2)
		except IOError as e:
			print "Failed to update .snose index file"
			#Don't need to do anything else)


def sneeze(snclient, key, filename):
	#place an existing note in current directory
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		#Doesn't exist so create new
		snose = {}
	#Get remote note
	try:
		remote = snclient.get_note(key)	
	except IOerror as e:
		print "Failed to find that note on Simplenote"
		print e
	else:
		#Write file
		try: 
			with open(filename, 'w') as f:
				f.write(remote[0]['content'])
		except IOError as e:
			print "Failed to create local copy of that note"
			print e
		else:
			#Update index
			try:
				snose[filename] = {'key': remote[0]['key'], 'syncnum': remote[0]['syncnum'], 'version': remote[0]['version'], 'modifydate': float(os.path.getmtime(filename)) } #Need to set as local modified date as otherwise will want to sync it straight away.
				#Write back out
				with open('.snose', 'w') as f:
					json.dump(snose, f, indent=2)
			except IOError as e:
				 print "Failed to update .snose index file"
				 print "But note was created locally. Try sniffing the file to add it to the index."


def blow(snclient, key):
	#With given key from .snose file, roll back to the previous version

	#1) Check exists in .snose index
	#2) Get previous version of remote
	#3) Write it out locally
	#4) Use that to update remote
	#5) Update index file with results

	#1) Check exists in .snose index
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
		#Need to get filename of note, loop through, performance should be fine as .snose likely to be small
		filename = [name for name, local in snose.iteritems() if local['key'] == key][0]
		print "Attempting to rollback file %s" % filename
	except IOError as e:
		print "Note doesn't exist in local .snose index"
	else:
		#2) Get previous version of remote
		try:
			#fetch once to know version
			remote = snclient.get_note(key)
			rollback = snclient.get_note(key, remote[0]['version']-1)
		except IOError as e:
			print "Failed to fetch previous version"
		else:
			try: 
				#3) Write it out locally
				with open(filename, 'w') as f:
					f.write(rollback[0]['content'])
				print "Rolled back local copy"
			except IOError as e:
				print "Failed to rollback local copy of that note"
				print e
			else:
				#Since rollback doesn't include full meta data, update remote accordingly
				try:
					del remote[0]['syncnum']
					del remote[0]['version']
				except KeyError:
					pass
				finally:
					#Set modified date
					sysmodifydate = float(os.path.getmtime(filename))
					remote[0]['modifydate'] = sysmodifydate
					remote[0]['content'] = rollback[0]['content']
					#4) Use that to update remote
					try:
						returned = snclient.update_note(remote[0])
						print "Rolled back remote version"
					except IOError as e:
						print "Failed to roll back remote version"
					else:
						#Get returned metadata
						snose[filename]['syncnum'] = returned[0]['syncnum']
						snose[filename]['version'] = returned[0]['version']
						snose[filename]['modifydate'] = sysmodifydate
						try:
							#5) Update index file with results
							with open('.snose', 'w') as f:
								json.dump(snose, f, indent=2)
						except IOError as e:
							 print "Failed to update .snose index file"
							 print "Try running a sync to get index corrected."


def snot(snclient):
	#List simplenote notes tagged with "snose"
	notelist = snclient.get_note_list()
	#That gets list of keys. Then need to iterate through and get first line of text.
	#This is going to be slow.
	print "Key:                               \tNote"
	for note in notelist[0]:
		if ("snose" in note['tags']) & (int(note['deleted']) != 1):
			#get note itself
			remote = snclient.get_note(note['key'])
			print remote[0]['key']  + " \t" + remote[0]['content'].splitlines()[0]


def sync(snclient, dry=False):
	#Need to read in mappings and sync those notes.
	dryremotes = []
	try:
		with open('.snose', 'r') as f:
			snose = json.load(f)
	except IOError as e:
		print 'Error reading Index file'
	else:
		#Need to iterate through list.
		for name, local in snose.iteritems():
			#First of all check for local modifications
			sysmodifydate = float(os.path.getmtime(name))
			if sysmodifydate > float(local['modifydate']): #ensure full timestamp
				if not dry:
				#Update remote
					try:
						with open(name, 'r') as f:
							content = f.read()
					except IOError as e:
						print "Failed to read local note %s" % name
						print "Skipping synchronisation for this note"
					else: 
						try:
							returned = snclient.update_note({'key': local['key'], 'version': local['version'], 'content': content, 'modifydate': sysmodifydate })
							print "Updated remote version of %s" % name
						except IOError as e:
							print "Failed to update remote verison of local note %s" % name
						else:
							#Get returned metadata
							snose[name]['syncnum'] = returned[0]['syncnum']
							snose[name]['version'] = returned[0]['version']
							snose[name]['modifydate'] = sysmodifydate #Use local value to avoid differences in accuracy (decimal places. etc) between local and remote timestamps
							#Update local file if merged content
							if 'content' in returned[0]:
								try:
									with open(name, 'w') as f:
										f.write(returned[0]['content'])
									print "Merged local content for %s" % name
									#Override the returned value? As otherwise next sync will immediately update the remote version for no reason.
									snose[name]['modifydate'] = os.path.getmtime(name) 
								except IOError as e:
									print "Failed to merge content locally for %s" % name
									print "Therefore skipping updating the index for this note" #I think this is a good idea?
							#Update the index file
							try:
								with open('.snose', 'w') as f:
									json.dump(snose, f, indent=2)
							except IOError as e:
								print "Failed to update index for changes regarding local file %s" % name
								print "But remote and local copy of the file itself have been updated."
								#What now? I don't know.
				elif dry:
					print "Updated remote version of %s" % name
					#For dry run, collect list of "updated remotes" to ignore in local updates
					dryremotes.append(name)
			#Fetch details from Simplenote
			try:
				remote = snclient.get_note(local['key'])
			except IOError as e:
				print "Failed to fetch remote copy of note %s" % name
				print "Skipping synchronisation for this file"
			else:
				if remote[0]['syncnum'] > local['syncnum']:
					if not dry:
						try: 
							with open(name, 'w') as f:
								f.write(remote[0]['content'])
							print "Updated local version of %s" % name
						except IOError as e:
							print "Failed to update local note %s with remote content" % name
							print "Will not updatet the .snose index file for this file"
						else:
							#Also update .snose index
							snose[name]['syncnum'] = remote[0]['syncnum']
							snose[name]['version'] = remote[0]['version']
							snose[name]['modifydate'] = os.path.getmtime(name) #As if set remote modify date, local file will immediately appear 'modified'
							try:
								with open('.snose', 'w') as f:
									json.dump(snose, f, indent=2)
							except IOError as e:
								print "Failed to update index"
								print "But local copy of the file %s has been updated with remote changes" % name
							#Some feedback
					elif (dry and (not (name in dryremotes))):
						print "Updated local version of %s" % name


main()
