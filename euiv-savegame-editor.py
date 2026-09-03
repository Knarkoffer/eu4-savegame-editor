"""
---------------------------------

Europa Universalis 4 - Savegame Editor Script

Version: 68

Script created to edit savegames of the Paradox-game Europa Universalis 4,
choose arguments to decide what things to edit.

Copyright (c) Knarkoffer 2015

This script is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This script is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

---------------------------------
"""


import hashlib
import sys
import os
import glob
import winreg
import argparse

print ('\r')
print ('Europa Universalis 4 - Savegame Editor Script (v68)')
print ('Copyright (c) Knarkoffer 2015')
print ('\r')


#

def smart_print(outString, verboseOnly):
	
	if verboseOnly and verboseMode:
		print(outString)
	elif not verboseOnly:
		print(outString)
	#
	
#


def assure_valid_savefile(filePath):
	
	correctStart = False
	
	savefileName = os.path.basename(filePath)
	savefileShortName, savefileExtension = os.path.splitext(savefileName)
	
	# Checks if the supplied file has an extension of .eu4
	
	with open(filePath, mode='r') as infile:
		first_line = infile.readline().strip()
		if first_line == 'EU4txt' and savefileExtension.lower() == '.eu4':
			correctStart = True
		#
	#
	
	return correctStart
#

	
# Opens and reads a line from a text-file, returns a string
def readLine(file_name, line_num):
	lines = open(file_name, mode='r').readlines()
	line = lines[line_num]
	return line;


# Checks if a string is number, returns a boolean
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
	#
#


## PARSER INFO

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('-p' ,'--path', type=str, default="", help=r'[Optional: Path where you keep the save files stored. Example: -p "C:\Games\EU4 Saves". Default will attempt to get the default location (usually something like C:\Users\Knarkoffer\Documents\Paradox Interactive\Europa Universalis IV\save games)]')
parser.add_argument('-f' ,'--file', type=str, default="", help='[Optional: Save-file to edit (including full path). Example: -f "C:\Games\EU4 Saves\Hansa1267_12_01.eu4"')
parser.add_argument('-ag' ,'--addGold', type=str, default="", help='How much gold to add to your treasury. Example: -ag 5000 ')

parser.add_argument('-mp' ,'--monarchPoints', action='store_true', default=False, help="Maximise Monarch points - Changes monarch points to 999")
parser.add_argument('-dc' ,'--deCore', action='store_true', default=False, help="deCore - Removes other countries cores from provinces you own")
parser.add_argument('-nl' ,'--naturalize', action='store_true', default=False, help="Naturalize - Changes culture of your owned provinces to your primary culture")
parser.add_argument('-sl' ,'--stabilize', action='store_true', default=False, help="Stabilize - Stabilizes the country by setting Legitimacy to 100 and Stability to 3")
parser.add_argument('-pr' ,'--prestigious', action='store_true', default=False, help="Prestigious - Sets the prestige to 100")
parser.add_argument('-gm' ,'--giftedmonarch', action='store_true', default=False, help="Gifted Monarch - Improved your monarch by maximising their stats")
parser.add_argument('-ma' ,'--maximizearmy', action='store_true', default=False, help="Maximize Army - Maxes both Manpower and Sailors")
parser.add_argument('-a' ,'--all', action='store_true', default=False, help="Just fixes everything!")
parser.add_argument('-v' ,'--verbose', action='store_true', default=False, help='Verbose mode - Prints lots of data')

# -- Convert input arguments to variables
args = parser.parse_args()    

# --path :
savePath = args.path

# --file :
saveFile = args.file

# --addGold :
addGold = args.addGold

if not is_number(addGold):
	print('Please ensure that the ammount is only numbers')
	addGold = ''
#

# --editMP
editMP = args.monarchPoints

# --editCores
editCores = args.deCore

# --editCulture
editCulture = args.naturalize

# --editStability
editStability = args.stabilize

# --editPrestige
editPrestige = args.prestigious

# --editMonarch
editMonarch = args.giftedmonarch

# --editMonarch
editManpower = args.maximizearmy

# --editAll
editAll = args.all

# --editAll
verboseMode = args.verbose

if editAll:
	addGold = '150000'
	editMP = True
	editCores = True
	editCulture = True
	editMonarch = True
	editManpower = True
	editStability = True
	editPrestige = True
#


## Makes sure the user has selected a mode
if not any([editMP, editCores, editCulture, editStability, editPrestige, editMonarch, editManpower, addGold]):
	
	sys.exit('No usage options selected, please see -h or --help for information' + '\r\n' + 'on how to use the script')
	
#


savefileName = ''
savefileNameShort = ''
savefileExtension = ''

saveToEdit = ''
saveEdited = False

if not(saveFile==''):

	# Makes sure the file exists
	if os.path.isfile(saveFile):
		
		# Argument was supplied, interpret this file
		saveToEdit = saveFile
		
		# Gets the folder of this save
		savePath = os.path.dirname(saveFile)
		
		savefileName = os.path.basename(saveToEdit)
		savefileNameShort = os.path.splitext(savefileName)[0]
		savefileExtension = os.path.splitext(savefileName)[1]
		
		# Checks if the supplied file has an extension of .eu4
		if savefileExtension.lower() == '.eu4'.lower():
			
			# Save has a correct file-sxtension
			print ('Selected savegame ' + savefileName + '\r\n')
			
		else:
			
			# Save has an incorrect file-extension, exists script
			sys.exit('Filename is wrong file-extension, needs to be .eu4\r\n')
		
	else:
		sys.exit('File supplied with -f does not exist\r\n')
	#

else:
	
	# user did not select a file, maybe a path?
	
	
	#user left path blank, attempt to get std path
	if (savePath == ''):
		
		
		#Default Path for Europa Universalis 4
		hKey = winreg.OpenKey (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')
		value, type = winreg.QueryValueEx (hKey, 'Personal')
		defaultPath = value + r'\Paradox Interactive\Europa Universalis IV\save games'
		defaultPath = os.path.expandvars(defaultPath)
		
		if not(os.path.isdir(defaultPath)):
			
			#Standard path does not exist, please write your path here:
			# Example: myPath = r'C:\Games\EUIV\save games'
			myPath = ''
			
			
			# If script directory has a "save game"-folder (used in developement fo script)
			if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save games')) and not myPath:
				myPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save games')
			#
			
			if (myPath==''):
				sys.exit('Neither path nor file was supplied, and the standard location of Documents\Paradox Interactive\Europa Universalis IV\save games does not exist,' + '\r\n' + 'please edit the script and define the variable myPath')
			else:
				savePath = myPath
			#
			
		else:
			savePath = defaultPath
	
	else:
		if not(os.path.isdir(savePath)):
			sys.exit('Folder "' + savePath + '" does not exist, please try again')
		#
	#
	
	import socket
	hostName = str(socket.gethostname()).upper()
	if hostName == 'SEGOTW10288286':
		savePath = r'C:\Data\Privat\EUIV_Saves'
	#
	
	#intSaves = glob.iglob(os.path.join(savePath, '*.eu4'))
	if not (len(glob.glob(os.path.join(savePath, '*.eu4'))) == 0):
		
		saveToEdit = max(glob.iglob(os.path.join(savePath, '*.eu4')), key=os.path.getctime)

		# Grabs the filename of savefile
		savefileName = os.path.basename(saveToEdit)
		savefileNameShort = os.path.splitext(savefileName)[0]
		savefileExtension = os.path.splitext(savefileName)[1]

		print ('No specific save selected, use latest save (' + savefileName + ')\r\n')
		
	else:
		sys.exit('No saves exist in folder ' + savePath + '\r\n')
	#
#


## Verifies that the save is indeed correct and is not of the compressed variety
if not assure_valid_savefile(saveToEdit):
	sys.exit('Save not identified as a valid EU4 (uncompressed format) file, exiting...\r\n')
#

## Reads the save in to an array

arrBaseSave = []
with open(saveToEdit, mode='r') as f:
	for line in f:
		arrBaseSave.append(line)
	#
#



# Saves the array to a new name, we'll never touch the basesave-one

arrEditedSave = []
arrEditedSave = arrBaseSave

# GETS COUNTRY VARIABLES

# Gets player country tag
playerCountryTag = arrEditedSave[3].strip().replace('player=', '').replace('"', '').strip()
playerCountryName = arrEditedSave[4].strip().replace('displayed_country_name=', '').replace('"', '').strip()

# Gets the players culture
playerCountryCulture = ''
bolFoundCountry = False

for (i, line) in enumerate(arrEditedSave):
	
	currentLine = line
	if '\t' + playerCountryTag + '={' in currentLine:
		if 'human=yes' in str(arrEditedSave[i + 1]):
			bolFoundCountry = True
		#
	#
	
	if bolFoundCountry:
		if '\tprimary_culture=' in currentLine:
			playerCountryCulture = currentLine.strip().replace('primary_culture=', '').replace('"', '')
			bolFoundCountry = False
		#
	#
#

bolFoundCountry = False




## EDIT MP
if editMP:
	
	print('-mp switch used, will now attempt to edit the Monarch Points (ADM, DIP, MIL)\r\n')
	
	# Script variables
	currentMP = ''
	currentMPA = 0
	currentMPD = 0
	currentMPM = 0
	
	targetMPA = 999
	targetMPD = 999
	targetMPM = 999
	
	monarchPointslineNumber = 0
	
	#Opens the file to search for the line known containing 'interesting_countries', which appears right after the monarch points
	for (i, line) in enumerate(arrEditedSave):
		
		currentLine = line
		
		# If the current line contains the string we are looking for ('interesting_countries')
		if 'interesting_countries={' in line:
			
			# Takes the line number subtracts 3, to identify the line with MP's
			monarchPointslineNumber = i - 2
		#
	#
	
	#Processes currentMP-string to get them nicely sorted
	currentMP = arrEditedSave[monarchPointslineNumber].strip().split(' ')
	currentMPA = int(currentMP[0])
	currentMPD = int(currentMP[1])
	currentMPM = int(currentMP[2])
	
	#if currentLegitimacy != targetLegitimacy:
	if (currentMPA + currentMPD + currentMPM < targetMPA + targetMPD + targetMPM):
		
		#arrEditedSave[monarchPointslineNumber] = '\t\t\t'+ str(targetMPA) + ' ' + str(targetMPD) + ' ' + str(targetMPM) + ' \r'
		arrEditedSave[monarchPointslineNumber] = str(arrEditedSave[monarchPointslineNumber]).replace(str(currentMPA), str(targetMPA))
		arrEditedSave[monarchPointslineNumber] = str(arrEditedSave[monarchPointslineNumber]).replace(str(currentMPD), str(targetMPD))
		arrEditedSave[monarchPointslineNumber] = str(arrEditedSave[monarchPointslineNumber]).replace(str(currentMPM), str(targetMPM))
		
		# Informs the user of the summarized results
		smart_print('\t' + 'Monarch points was: \r\n\t' + 'ADM: ' + str(currentMPA) + '\r\n\t' + 'DPL: ' + str(currentMPD) + '\r\n\t' + 'MIL: ' + str(currentMPM), True)
		smart_print('', True)
		smart_print('\t' + 'Monarch points modified to: \r\n\t' + 'ADM: ' + str(targetMPA) + '\r\n\t' + 'DPL: ' + str(targetMPD) + '\r\n\t' + 'MIL: ' + str(targetMPM), False)
		smart_print('', False)
		
		saveEdited = True
		
	else:
		
		smart_print('\t' + playerCountryName + ' had a maximum points, nothing edited', True)
		smart_print('', True)
		
	#

#

if editCores:

	# -dc switch, works by rebuilding the save, drops lines containing core= (except yours ofc) in owned provinces.
	# Was the most difficult to get right, to ignore non-owned provinces and handle provinces with troops stationed
	# in them
	
	print('-dc switch used, will now attempt to de-core your provinces' + '\r\n')
	
	#Creates a new array, to contain the whole save
	arrRebuiltSave = []
	
	# Variables:
	
	# Bool to help remember if the province being looked at is owned by player
	ownedProvince = False
	provinceEdited = False
	
	# Counts to give a nice, summarized output
	provinceCountOwned = 0
	provinceCountEdited = 0
	
	# Keeps track if the line should be ignored or not
	ignoreLine = False
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		# Assumes line is not to be ignored
		ignoreLine = False
		
		# If the line contains owner=, and previous line contained name=, it's a province
		if ('owner="' in currentLine) and ('name="' in str(arrEditedSave[i - 1])):
			
			# if the line does contain the players tag, it's a valid province
			if '"' + playerCountryTag + '"' in currentLine:
			
				# Province is owned by the player
				ownedProvince = True
				provinceCountOwned = provinceCountOwned + 1
				
				#Saves the province name
				provinceName = str(arrEditedSave[i - 1]).strip().replace('name=', '').replace('"', '')
				
				#print ('\t' + playerCountryTag + ' province found: ' + provinceName)
			
			#Ignore other countris provinces
			else:
				#print ('\t' + 'Province not owned by ' + playerCountryTag + ', but owned by= ' + line.strip().replace('owner=', '').replace('"', ''))
				ownedProvince = False
		
		#If the province is owned by the player
		if ownedProvince:
			
			provinceEdited = False
			
			if str(arrEditedSave[i - 1]).rstrip() == '\t\t' + 'cores={':
				
				coreList = currentLine.strip().split()
				
				for tagCore in coreList:
					if not tagCore == playerCountryTag:
						provinceEdited = True
						print ('\t' + provinceName + ' had a core from ' + tagCore + ' removed')
						arrEditedSave[i] = str(arrEditedSave[i]).replace(tagCore, '')
						saveEdited = True
					#
				#
				
				# Edits the array
				arrEditedSave[i] = str(arrEditedSave[i]).replace(' ', '')
				
			#
			
			if provinceEdited:
				provinceCountEdited = provinceCountEdited + 1
			#
		#
	#
	
	# Informs the user of the summarized results
	print('')
	print('\t' + 'A total of ' + str(provinceCountEdited) + ' of your ' + str(provinceCountOwned) + ' provinces was de-Cored' + '\r\n')
	print('')



if (editCulture):
	
	# -nl switch, works by finding your provinces and changing the culture in them to your countrys standard
	
	print('-nl switch used, will now attempt naturalize (change culture) your provinces' + '\r\n')
	
	# Informs the user of the idientified standard culture. This might not be correct, haven't had the 
	# opportunity to check how it works for reformed countries (like Sweden -> Scandinavia or Teutonic Order -> Prussia)
	print('\t' + 'Primary culture identified as ' + playerCountryCulture + '\r\n')
	
	# Bool to help remember if the province being looked at is owned by player
	ownedProvince = False
	bolProvinceFixed = False
	
	# Counters to give a nice, summarized output
	provinceCountOwned = 0
	provinceCountEdited = 0
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		if '\towner="' in currentLine:
			
			if 'name="' in str(arrEditedSave[i - 1]):
			
				#Saves the province name
				provinceName = str(arrEditedSave[i - 1]).strip().replace('name=', '').replace('"', '')
			
				if '"' + playerCountryTag + '"' in currentLine:
					
					ownedProvince = True
					bolProvinceFixed = False
					
					#print ("Your province found: " + provinceName)
					
					provinceCountOwned = provinceCountOwned + 1
					
				else:
					
					#print ("Province "+ provinceName +" not owned by " + playerCountryTag + ", but owned by " + currentLine.strip().replace('owner=', '').replace('"', '') + ", do nothing")
					
					ownedProvince = False
					bolProvinceFixed = True
				#
			#
		#
		
		if ownedProvince:
			
			if not bolProvinceFixed:
				
				if currentLine.startswith('\t\t' + 'culture='):
					
					if (str(arrEditedSave[i - 1]).startswith('\t\t' + 'original_culture=')) and (str(arrEditedSave[i + 1]).startswith('\t\t' + 'religion=')):
						
						if not currentLine.strip() == 'culture=' + playerCountryCulture:
							
							# Gets the current culture of the province
							currentCulture = currentLine.strip().split('=')[1].strip()
							currentCultureHuman = str(' '.join(i.capitalize() for i in currentCulture.split('_')))
							
							# Edits the array by replacing i line with a modified line,
							# where the provinces current culture was replaced by the
							# players current culture
							arrEditedSave[i] = str(arrEditedSave[i]).replace(currentCulture, playerCountryCulture)
							
							# Informs the user of action taken
							smart_print('\t' + provinceName + ' (' + currentCultureHuman + ') found', False)
							
							#Notes that the province was fixed, and increments counter
							bolProvinceFixed = True
							provinceCountEdited = provinceCountEdited + 1
							
						else:
							#print(provinceName + ' already correct culture')
							bolProvinceFixed = True
						#
					#
				#
			#
		#
	#
	
	if provinceCountEdited > 0:
		# Informs the user of the summarized results
		smart_print('', False)
		smart_print('\t' + 'A total of ' + str(provinceCountEdited) + ' of your ' + str(provinceCountOwned) + ' provinces was naturalized' + '\r\n', False)
		smart_print('', False)
		
		saveEdited = True
		
	else:
		smart_print('No provinces naturalized', True)
	#
	
#


if (editMonarch == True):
	
	# -gm switch, grants your current monarch maximum good stats
	
	print("-gm switch used, will now attempt to locate your monarch and improve him" + "\r\n")
	# \tENG={
	
	# Bool keep track if we are in country
	blnInCountry = False
	
	# Counters to give a nice, summarized output
	monarchName = ''
	monarchLine = 0
	
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		if (currentLine.startswith('\t\thuman=yes')) and (str(arrEditedSave[i - 1]) == '\t' + playerCountryTag + '={\n'):
			#print ('Entered ' + playerCountryTag + ' at' + str(i))
			blnInCountry = True
			
			
		if blnInCountry and (currentLine == "\t}\n"):
			blnInCountry = False
			#print ('Exited ' + playerCountryTag + ' at' + str(i))
		
		
		if blnInCountry:
			
			# This saves infor for each monarch, therefore monarchName and monarchLine will always contain the last monarch.
			# While this is not optimal, it works. Maybe a better approach would  be to build an array, and read it backwards?
			if ('\t' + 'heir={' in currentLine) and (playerCountryTag in str(arrEditedSave[i + 6])):
				
				monarchName = str(arrEditedSave[i + 5]).strip().replace('name=', '').replace('"', '').strip()
				monarchLine = i + 5
				
				# Informs the users what rulers for the nation save contains, silenced for now
				smart_print('Found monarch ' + monarchName + " @ " + str(i + 1), True)
				
			#
		#
	#
	
	# Now edits the last monarch
	#'DIP=' = monarchLine + 2
	#'ADM=' = monarchLine + 3
	#'MIL=' = monarchLine + 4
	
	if not (monarchLine == 0):
		
		targetMonarchDIP = 9
		targetMonarchADM = 9
		targetMonarchMIL = 9
		
		currentMonarchDIP = int(str(arrEditedSave[monarchLine + 2]).strip().replace('DIP=', ''))
		currentMonarchADM = int(str(arrEditedSave[monarchLine + 3]).strip().replace('ADM=', ''))
		currentMonarchMIL = int(str(arrEditedSave[monarchLine + 4]).strip().replace('MIL=', ''))
		
		if (currentMonarchDIP + currentMonarchADM + currentMonarchMIL < targetMonarchDIP + targetMonarchADM + targetMonarchMIL):
			
			arrEditedSave[monarchLine + 2] = arrEditedSave[monarchLine + 2].replace(str(currentMonarchDIP), str(targetMonarchDIP))
			arrEditedSave[monarchLine + 3] = arrEditedSave[monarchLine + 3].replace(str(currentMonarchADM), str(targetMonarchADM))
			arrEditedSave[monarchLine + 4] = arrEditedSave[monarchLine + 4].replace(str(currentMonarchMIL), str(targetMonarchMIL))
			
			# Informs the user of the summarized results
			smart_print('\t' + 'Monarch ' + monarchName + ' had: \r\n\tADM: ' + str(currentMonarchADM) + '\r\n\tDIP: ' + str(currentMonarchDIP) + '\r\n\tMIL: ' + str(currentMonarchMIL), False)
			smart_print('', False)
			smart_print('\t' + 'Monarch ' + monarchName + ' modified to: \r\n\tADM: ' + str(targetMonarchADM) + '\r\n\tDIP: ' + str(targetMonarchDIP) + '\r\n\tMIL: ' + str(targetMonarchMIL), False)
			smart_print('', False)
			
			saveEdited = True
			
		else:
		
			smart_print('No need to edit monarch ' + monarchName, True)
		#
	else:
		
		smart_print("Could not find any rulers/monarchs for country " + playerCountryName, True)
	#
#



if addGold:
	
	if not is_number(addGold):
		
		print("The sum of gold you are trying to add must be a number")
		
	else:
		
		# -ag switch, adds a user defined number of gold to your countrys treasury
		
		monarchName = ""
		
		print("-ag switch used, will now locate your country's treasury and add the desired amount to it" + "\r\n")
		# \tENG={
		
		# Bool keep track if we are in country
		blnInCountry = False
		
		# Iterate the arrEditedSave array line by line
		for (i, currentLine) in enumerate(arrEditedSave):
			
			if (currentLine.startswith('\t\thuman=yes')) and (str(arrEditedSave[i - 1]) == '\t' + playerCountryTag + '={\n'):
				#print ('Entered ' + playerCountryTag + ' at' + str(i))
				blnInCountry = True
			#
			
			if blnInCountry and (currentLine == "\t}\n"):
				#print ('Exited ' + playerCountryTag + ' at' + str(i))
				blnInCountry = False
			#
			
			if blnInCountry:
				
				# The lines being read belongs to the target nation
				if (currentLine.startswith('\t\ttreasury=')) and (str(arrEditedSave[i - 1]).startswith('\t\tstability=')) and (str(arrEditedSave[i + 1]).startswith('\t\testimated_monthly_income=')):
					
					# Converts the line to the actual sum of the treasury
					currentTreasury = float(currentLine.strip().replace('treasury=', ''))
					
					# Does the math operations
					addGold = float(addGold)
					targetTreasury = currentTreasury + addGold
					
					# Rounds the number down to 3 decimals (don't know what happens if you have more, but standard in EU4 is 3)
					targetTreasury = round(targetTreasury, 3)
					
					# Converts the sums to strings
					currentTreasury = str(currentTreasury)
					addGold = str(addGold)
					targetTreasury = str(targetTreasury)
				
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentTreasury, targetTreasury)
					
					# Informs the user of the summarized results
					smart_print('\t' + playerCountryName + ' had a treasury of: ' + currentTreasury + ", added " + addGold + " gold to it", False)
					smart_print('\t' + playerCountryName + ' treasury changed to: ' + str(targetTreasury), False)
					smart_print('', False)
					
					saveEdited = True
					
				#
			#
			
		#
	#
#




if editStability:
	
	print("-sl switch used, will now stabilize country" + "\r\n")
	
	# Bool keep track if we are in country
	blnInCountry = False
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		if (currentLine.startswith('\t\thuman=yes')) and (str(arrEditedSave[i - 1]) == '\t' + playerCountryTag + '={\n'):
			#print ('Entered ' + playerCountryTag + ' at' + str(i))
			blnInCountry = True
		#
		
		if blnInCountry and (currentLine == "\t}\n"):
			#print ('Exited ' + playerCountryTag + ' at' + str(i))
			blnInCountry = False
		#
		
		if blnInCountry:
			
			# The lines being read belongs to the target nation
			if (currentLine.startswith('\t\tstability=')) and (str(arrEditedSave[i - 1]).startswith('\t\tprestige=')) and (str(arrEditedSave[i + 1]).startswith('\t\ttreasury=')):
				
				currentStability = currentLine.strip().replace('stability=', '').strip()
				targetStability = '3.000'
				
				if currentStability != targetStability:
					
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentStability, targetStability)
					
					# Informs the user of the summarized results
					smart_print('\t' + playerCountryName + ' had a stability of: ' + currentStability + ', changed to ' + targetStability, False)
					smart_print('', False)
					
					saveEdited = True
					
				else:
					
					smart_print('\t' + playerCountryName + ' already had max stability, nothing edited', True)
					smart_print('', True)
					
				#
			#
			
			# The lines being read belongs to the target nation
			if (currentLine.startswith('\t\t' + 'legitimacy=')) and (str(arrEditedSave[i - 1]).startswith('\t\t' + 'root_out_corruption_slider=')) and (str(arrEditedSave[i + 1]).startswith('\t\t' + 'mercantilism=')):
				
				currentLegitimacy = currentLine.strip().replace('legitimacy=', '').strip()
				targetLegitimacy = '100.000'
				
				if currentLegitimacy != targetLegitimacy:
					
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentLegitimacy, targetLegitimacy)
					
					# Informs the user of the summarized results
					smart_print('\t' + playerCountryName + ' had a legitimacy of: ' + currentLegitimacy + ', changed to ' + targetLegitimacy, False)
					smart_print('', False)
					
					saveEdited = True
					
				else:
					
					smart_print('\t' + playerCountryName + ' already had max legitimacy, nothing edited', True)
					smart_print('', True)
					
				#
			#
			
			
		#
		
		
	#
#



if editManpower:
	
	print("-ma switch used, will now maximize army (available manpower & sailors)" + "\r\n")
	
	# Bool keep track if we are in country
	blnInCountry = False
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		if (currentLine.startswith('\t\thuman=yes')) and (str(arrEditedSave[i - 1]) == '\t' + playerCountryTag + '={\n'):
			#print ('Entered ' + playerCountryTag + ' at' + str(i))
			blnInCountry = True
		#
		
		if blnInCountry and (currentLine == "\t}\n"):
			#print ('Exited ' + playerCountryTag + ' at' + str(i))
			blnInCountry = False
		#
		
		if blnInCountry:
			
			# Edits manpower
			if (currentLine.startswith('\t\t' + 'manpower=')) and (str(arrEditedSave[i - 1]).rstrip() == '\t\t}') and (str(arrEditedSave[i + 1]).startswith('\t\t' + 'max_manpower=')):
				
				currentManpower = currentLine.strip().replace('manpower=', '').strip()
				maxManpower = str(arrEditedSave[i + 1]).strip().replace('max_manpower=', '').strip()
				maxManpowerHuman = str(float(maxManpower) * 1000).split('.')[0] #maxManpower.split('.')[0] + '000'
				
				if currentManpower != maxManpower:
					
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentManpower, maxManpower)
					
					# Informs the user of the summarized results
					print('\t' + 'Maximized manpower of ' + playerCountryName + ' to ' + maxManpowerHuman)
					print('')
					
					saveEdited = True
					
				else:
					
					print('\t' + playerCountryName + ' already had max manpower, nothing edited')
					print('')
					
				#
				
			#
			
			# Edits Sailors
			if (currentLine.startswith('\t\t' + 'sailors=')) and (str(arrEditedSave[i - 1]).startswith('\t\t' + 'max_manpower=')) and (str(arrEditedSave[i + 1]).startswith('\t\t' + 'max_sailors=')):
				
				currentSailors = currentLine.strip().replace('sailors=', '').strip()
				maxSailors = str(arrEditedSave[i + 1]).strip().replace('max_sailors=', '').strip()
				maxSailorsHuman = str(maxSailors).split('.')[0]
				
				if currentSailors != maxSailors:
					
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentSailors, maxSailors)
					
					# Informs the user of the summarized results
					print('\t' + 'Maximized sailors of ' + playerCountryName + ' to ' + maxSailorsHuman)
					print('')
					
					saveEdited = True
					
				else:
					
					print('\t' + playerCountryName + ' already had max sailors, nothing edited')
					print('')
					
				#
				
			#
			
		#
		
		
	#
#

if editPrestige:
	
	print("-pr switch used, will now grant maximum prestige" + "\r\n")
	
	# Bool keep track if we are in country
	blnInCountry = False
	
	# Iterate the arrEditedSave array line by line
	for (i, currentLine) in enumerate(arrEditedSave):
		
		if (currentLine.startswith('\t\thuman=yes')) and (str(arrEditedSave[i - 1]) == '\t' + playerCountryTag + '={\n'):
			#print ('Entered ' + playerCountryTag + ' at' + str(i))
			blnInCountry = True
		#
		
		if blnInCountry and (currentLine == "\t}\n"):
			#print ('Exited ' + playerCountryTag + ' at' + str(i))
			blnInCountry = False
		#
		
		if blnInCountry:
			
			# The lines being read belongs to the target nation
			if (currentLine.startswith('\t\t' + 'prestige=')) and (str(arrEditedSave[i - 1]).startswith('\t\t' + 'score_place=')) and (str(arrEditedSave[i + 1]).startswith('\t\t' + 'stability=')):
				
				currentPrestige = currentLine.strip().replace('prestige=', '').strip()
				targetPrestige = '100.000'
				
				if currentPrestige != targetPrestige:
					# Edits the array
					arrEditedSave[i] = str(arrEditedSave[i]).replace(currentPrestige, targetPrestige)
					
					# Informs the user of the summarized results
					print('\t' + playerCountryName + ' had a prestige of: ' + currentPrestige + ', changed to ' + targetPrestige)
					print('')
					
					saveEdited = True
				
				else:
					
					print('\t' + playerCountryName + ' already had max prestige, nothing edited')
					print('')
					
				#
			#
			
			
			
		#
		
		
	#
#


#myList = ['asd','dss']
#print('HASH: ' + str(hash(tuple(myList))))

def totalList(lst):
	return reduce(lambda x,y:x+y, lst)
#

## Writes the array arrEditedSave to a new file on disk, located in either the save folder or the same folder as the input file
# User has used an option, this means that file was edited and needs to be saved
if saveEdited:

	#Generates a new save name (Example: basename_mod.ext)
	newSaveName = os.path.join(savePath, savefileNameShort + "_mod" + savefileExtension)
	
	# Informs the user
	print("Save edited, creating modified version (" + savefileNameShort + "_mod" + savefileExtension + ")")
	
	# Create an empty file
	with open(newSaveName, mode='w', encoding='cp1252', newline='') as outputFile:
	#with open(newSaveName, mode='w', newline='') as outputFile:
		
		# Writes lines from modified array to this new file
		for item in arrEditedSave:
			outputFile.write(item)
		#
	#
	
else:
	print('Nothing changed, no need to edit savefile')

#


# Script is complete, exit it
print ("\r\n" + "The End!" + '\r\n' + "Thanks for using my script!" + "\r\n")


