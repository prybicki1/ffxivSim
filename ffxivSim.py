from __future__ import division
import gspread #https://github.com/burnash/gspread
from oauth2client.service_account import ServiceAccountCredentials

'''
BARD CLASS
'''
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
		self.crit_dmg_mod = 1.45
		self.crit_chance = 0.5
		self.crit_chance_mod = 1
		self.dhit_chance = 0.5
		self.dhit_dmg_mod = 1.4
		self.auto_time = 2500
		self.auto_pot = 75

		self.dots = []


	#return a list of entries that are available for use
	def getUseableSkills(self):
		useableSkills = []
		for entry in self.skillData:
			if entry['cd_timer'] == 0:
				useableSkills.append(entry)
		return useableSkills

	#use a skill, return the potency dealt and time passed TODO: returned potency must account for crits
	def useSkill(self,skillName):
		retVal = {'potency':0,'time':0}
		for i in range(len(self.skillData)):
			if self.skillData[i]['skill_name'] == skillName:
				if self.skillData[i]['cd'] == 'GCD' and self.skillData[i]['cd_timer'] == 0:
					#set all gcds on cd
					self.gcdUsed()
					#decrement timers
					retVal['time'] = self.decrementTimers(self.skillData[i]['cast_time'])
					#if a dot, add entry to dot table NOTE: make sure this code matches below
					if self.skillData[i]['dot_potency'] > 0:
						dotEntry = self.skillData[i]
						self.dots.append(dotEntry)
				elif self.skillData[i]['cd'] > 0 and self.skillData[i]['cd_timer'] == 0:
					#set on cd
					self.skillData[i]['cd_timer'] = self.skillData[i]['cd']
					#decrement timers
					retVal['time'] = self.decrementTimers(self.skillData[i]['cast_time'])
					#if a dot, add entry to dot table TODO: add the dot, reset if already there
					if self.skillData[i]['dot_potency'] > 0:
						dotEntry = self.skillData[i]
						dotEntry['dot_timer'] = dotEntry['dot_dura']
						dotEntry['tick_timer'] = 3000
						self.dots.append(dotEntry)
				retVal['potency'] = self.dealDamage(self.skillData[i]['potency'])
		return retVal

	#do nothing, return time passed
	def doNothing(self):
		minTime = 999999
		#find the lowest cd skill
		for i in range(len(self.skillData)):
			if self.skillData[i]['cd_timer'] < minTime:
				minTime = self.skillData[i]['cd_timer']

		return self.decrementTimers(minTime)

	#decrement timers method
	def decrementTimers(self,timePassed):
		for i in range(len(self.skillData)):
			if self.skillData[i]['cd_timer'] < timePassed:
				self.skillData[i]['cd_timer'] = 0
			else:
				self.skillData[i]['cd_timer'] -= timePassed
		return timePassed

	#reset GCD timer method
	def gcdUsed(self):
		for i in range(len(self.skillData)):
			if self.skillData[i]['cd'] == 'GCD':
				self.skillData[i]['cd_timer'] = self.GCD_TIME

	#TODO: calculate crit and dhit, then return the true potency
	#TODO2: repetoire stacks
	def dealDamage(self,potency):
		return potency

'''
SIMULATOR
'''
#get the names of skills within a list of skills
def getEntryNames(useList):
	for entry in useList:
		print entry['skill_name']

#mock sim
total_potency = 0
total_time = 0

#create the simulator class
sim = Bard()

while total_time < 180000:
	useList = sim.getUseableSkills()

	print getEntryNames(useList)
	skillName = raw_input('Enter which skill you would like to use: ')

	skillResu = {'time':0,'potency':0}

	if skillName != 'None':
		skillResu = sim.useSkill(skillName)
	else:
		skillResu['time'] = sim.doNothing()

	total_potency += skillResu['potency']
	total_time += skillResu['time']


print 'total_potency: ', total_potency
print 'total_time(ms): ', total_time
print 'total PPS: ', total_potency / (total_time / 1000)