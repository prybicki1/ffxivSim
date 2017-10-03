import gspread #https://github.com/burnash/gspread
from oauth2client.service_account import ServiceAccountCredentials

class Bard(object):
	def __init__(self):
		#create login credentials and connect the client
		scope = ['https://spreadsheets.google.com/feeds']
		creds = ServiceAccountCredentials.from_json_keyfile_name('pracSheets_cred.json', scope)
		client = gspread.authorize(creds)

		#get the sheet as an object
		sheet = client.open('bardSkillDataBase').sheet1

		#2d list representation of the sheet, in this case, all our abilities
		self.skillData = sheet.get_all_records()

		#constants TODO: get these values from gspreadsheets for more accuracy
		self.GCD_TIME = 2500
		self.sks_mod = 1
		self.dmg_mod = 1
		self.crit_mod = 1
		self.auto_time = 2500
		self.auto_pot = 75
		#self.dots += AutoEntry


	#return a list of entries that are available for use
	def getUseableSkills():
		for entry in self.skillData:
			if entry['cd_timer'] == 0:
				useableSkills += entry
		return useableSkills

	#use a skill, return the potency dealt TODO: returned potency must account for crits
	def useSkill(skillName):
		for entry in self.skillData:
			if entry['skill_name'] == skillName:
				if entry['cd'] == 'GCD':
					#TODO: start gcd timer
					#TODO: decrement timers
					#if a dot, add entry to dot table
					if entry['dot_potency'] > 0:
						dotEntry = entry
						dots += dotEntry
				else if entry['cd'] > 0:
					#set on cd
					#TODO: decrement timers
					#if a dot, add entry to dot table TODO: add the dot, reset if already there
					if entry['dot_potency'] > 0:
						dotEntry = entry
						self.dots += dotEntry
				return entry['potency']

	#TODO: decrement timers method

	#TODO: reset GCD timer method


'''
SIMULATOR
'''

#mock sim
total_potency = 0
total_time = 0

print 'total_potency: ', total_potency
print 'total_time: ', total_time
print 'total PPS: ', total_potency / (total_time / 100)