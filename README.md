#SNose - Simplenote Object Synchronisation (Explicit)

A command line client / python script using the [Simplenote.py](https://github.com/mrtazz/simplenote.py) module from [mrtazz (Daniel Schauenberg)](https://github.com/mrtazz) that allows you to synchronise just the (text) files you specify within a directory across multiple machines.

##FAQ

1. You thought of the name "snose" first and then tried to wangle in something to make it an acronym, didn't you? *Yes.*


##Inspiration

Basically I wanted a way to synchronise arbitrary "dotfiles" without the "expense" of a Git repository:

- Git seems a bit overkill
- I'm not really bothered about versioning, just synchronisation
- I just want to synchronise *some* files within a directory, not all of them (just imagine the `.gitignore`!)

##How to use

###In general - Authentication

Probably the best way is just to supply your username and password like so:

    python snose.py --username=me@email.com --password=mypassword

In theory snose also supports having your password in plain text (in json format) in a file called `.snoseauth`. But I haven't actually got around to testing this yet. Or thought of a token based approach as I'd need to modify simplenote.py.

###Snort - Importing a new file

Take a file from the current directory and import into Simplenote as a new note:

    python snose.py --username=<me@email.com> --password=<mypassword> --snort=<filename.ext>

###Sniff - Importing an existing file

Take a file from the current directory and "match" it to an existing note within Simplenote

    python snose.py  --username=<me@email.com> --password=<mypassword> --sniff=<key> <filename.ext>

Where key is the id used by Simplenote to identify the note. So the best way to find this is to make sure the noted is tagged as "snose" in Simplenote and then you can use `snose.py --snot` to find the key.

###Sneeze - Export an existing file

Export a file from Simplenote to the current directory.

    python snose.py  --username=<me@email.com> --password=<mypassword> --sneeze=<key> <filename.ext>

###Sync - Synchronise files

Reads files in the `.snose` index file and synchronises them with Simplenote. 
    
	python snose.py  --username=<me@email.com> --password=<mypassword> --sync

You can pass the optional `--hanky` flag at the same time to perform a dry run; although the dry run can't indicate when merging will occur, only the ultimate direction of the update.

    python snose.py  --username=<me@email.com> --password=<mypassword> --sync --hanky


###Snot - List files available for synchronisation with SNose

Lists all files on Simplenote tagged "snose":

    python snose.py  --username=<me@email.com> --password=<mypassword> --snot

I could do with making this also list what is currently being synchronised based on the index. 

##How it works

It's really quite simple (after all, I've done it), basically it creates a `.snose` file in the current directory that is json formatted. This is basically a Python dictionary that maps a filename (from the current directory) to a simplenote note (via the key) and also includes other simplenote data such as the modification date, version number and sync number (so it can figure out how to sync).

It then just implements the Simplenote recommendation from the api:

1. Iterates through each file stored in the `.snose` index.
2. First of all looks for local modifications (compares modification date of the file with what is stored in the index). 
3. Then attempts to update the remote version on Simplenote, but will merge the content if the remote has also changed. If merging occurs both the local and remote are updated.
4. Then checks for remote updates by comparing version numbers and updates local copies if necessary.


##To Do

- Files in subdirectories, what happens there? I've just assumed all files in same directory as index
- Using tags to contain filename: "filename:pants.txt" Some potential character limitations though? But an interesting idea for meta data.
- Add ability to "snort" multiple files"
- List files currently being synchronised (read the .snose index). The `--snot` lists files tagged *snose* on Simplenote and the two might not necessarily be the same (i.e you've chose to sync some files on one machine and a different set on another).
- Write updated index file once after sync, instead of writing for each file change (although writing per file does have it's advantage from an error handling point of view)
 
