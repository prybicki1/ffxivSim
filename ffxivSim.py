from __future__ import division
import gspread #https://github.com/burnash/gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

'''
BARD CLASS
	-Make this into a seperate file when done
	-Superclass for all job constants?
	-Spreadsheet accessable from here:
		https://docs.google.com/spreadsheets/d/1Nt9yikNSAOUwf2pChTUct4Su6aeuk-9u32iVFeMeUPU/edit?usp=sharing
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

		#crit stat data
		sheet = client.open('FFXIV 70 Statistic Intervals').worksheet('Crit')

		#make crit chart sheet
		self.critData = sheet

		#dhit stat data
		sheet = client.open('FFXIV 70 Statistic Intervals').worksheet('Direct Hit')

		#make dhit chart sheet
		self.dhitData = sheet

		#constants TODO: get these values from gspreadsheets for more accuracy
		self.GCD_TIME = 2500
		self.TICK_RATE = 3000

		#stats
		self.CRT = 2000
		self.DHIT = 1000
		self.SKS = 1000

		self.sks_mod = 1
		self.dmg_mod = 1
		self.crit_dmg_mod = float(self.critData.cell(self.CRT - 361, 4).value) + 1.0
		self.crit_chance = float(self.critData.cell(self.CRT - 361, 3).value) * 100.0
		self.crit_chance_mod = 1
		self.dhit_chance = float(self.dhitData.cell(self.DHIT - 361, 3).value) + 1.0
		self.dhit_chance_mod = 1
		self.dhit_dmg_mod = 1.25

		#array of currently applied dots, start with the auto_attack entry
		self.dots = [self.skillData[0]]
		self.skillData.pop(0)

		#array of buffs
		self.buffs = []


	#return a list of entries that are available for use
	def getUseableSkills(self):
		useableSkills = []
		for entry in self.skillData:
			if entry['cd_timer'] == 0:
				useableSkills.append(entry)
		return useableSkills

	#use a skill, return the potency dealt and time passed TODO: Buffs, then Refulgent
	def useSkill(self,skillName):
		#we'll return the potency dealt and the time passed
		retVal = {'potency':0,'time':0}
		for i in range(len(self.skillData)):
			if self.skillData[i]['skill_name'] == skillName:
				#GCD
				if self.skillData[i]['cd'] == 'GCD' and self.skillData[i]['cd_timer'] == 0:
					#set all gcds on cd
					self.gcdUsed()

					#if Iron Jaws, reset both dot timers
					if self.skillData[i]['skill_name'] == 'Iron Jaws':
						self.IronJawsReset()

					#decrement timers
					ticksAndTime = self.decrementTimers(self.skillData[i]['cast_time'])
					retVal['time'] += ticksAndTime['time']
					retVal['potency'] += ticksAndTime['potency']

					#if straight shot, apply straight shot buff
					if self.skillData[i]['skill_name'] == 'Straight Shot':
						self.applyBuff(self.skillData[i])
					
				#OGCD
				elif self.skillData[i]['cd'] > 0 and self.skillData[i]['cd_timer'] == 0:
					#set on cd, if BL or RoD, set both on CD
					if self.skillData[i]['skill_name'] == 'Bloodletter' or self.skillData[i]['skill_name'] == 'Rain of Death':
						self.setBloodAndRain()
					else:
						self.skillData[i]['cd_timer'] = self.skillData[i]['cd']
					#decrement timers
					ticksAndTime = self.decrementTimers(self.skillData[i]['cast_time'])
					retVal['time'] += ticksAndTime['time']
					retVal['potency'] += ticksAndTime['potency']

					#apply raging strikes of used
					if self.skillData[i]['skill_name'] == 'Raging Strikes':
						self.applyBuff(self.skillData[i])
						
				#if a dot, add entry to dot table, reset if already there
				if self.skillData[i]['dot_potency'] > 0:
					dotIndex = -1
					for j in range(len(self.dots)):
						if self.dots[j]['skill_name'] == self.skillData[i]['skill_name']:
							dotIndex = j
					#if dot is already applied
					if dotIndex >= 0:
						self.dots[dotIndex]['dot_timer'] = self.dots[dotIndex]['dot_dura']
						self.dots[dotIndex]['tick_timer'] = self.TICK_RATE
					#if dot is not applied
					else:
						dotEntry = self.skillData[i]
						dotEntry['dot_timer'] = dotEntry['dot_dura']
						dotEntry['tick_timer'] = self.TICK_RATE
						self.dots.append(dotEntry)

				retVal['potency'] += self.dealDamage(self.skillData[i])

		return retVal

	#do nothing, returns time passed and potency dealt by dots in that time
	def doNothing(self):
		minTime = 999999
		#find the lowest cd skill
		for i in range(len(self.skillData)):
			if self.skillData[i]['cd_timer'] < minTime and self.skillData[i]['cd_timer'] > 0:
				minTime = self.skillData[i]['cd_timer']

		if minTime == 999999:
			minTime = self.GCD_TIME

		return self.decrementTimers(minTime)

	#decrement timers method, returns dot potency dealt
	def decrementTimers(self,timePassed):
		retVal = {'time':0,'potency':0}

		for i in range(len(self.skillData)):
			#decrement CDs
			if self.skillData[i]['cd_timer'] < timePassed:
				self.skillData[i]['cd_timer'] = 0
			else:
				self.skillData[i]['cd_timer'] -= timePassed

		#dots management
		#fallen off dots names
		fallenOffDots = []
		for i in range(len(self.dots)):
			#decrement tick and full dot length
			self.dots[i]['dot_timer'] -= timePassed
			self.dots[i]['tick_timer'] -= timePassed
			#check if the tick timer has ticked
			if self.dots[i]['tick_timer'] <= 0:
				retVal['potency'] += self.dealDamage(self.dots[i])
				self.dots[i]['tick_timer'] += self.TICK_RATE
			#check if the dot has fallen off
			if self.dots[i]['dot_timer'] <= 0:
				fallenOffDots.append(self.dots[i])

		#remove fallen off dots
		for dot in fallenOffDots:
			if dot['skill_name'] != 'auto_attack':
				self.dots.remove(dot)

		#buffs management
		#fallen off buffs names
		fallenOffBuffs = []
		for i in range(len(self.buffs)):
			#decrement buff timer
			self.buffs[i]['buff_timer'] -= timePassed
			#check if buff has fallen off
			if self.buffs[i]['buff_timer'] <= 0:
				fallenOffBuffs.append(self.buffs[i])

		#remove fallen off buffs
		for buff in fallenOffBuffs:
			#undo straight shot
			if buff['skill_name'] == 'Straight Shot':
				self.crit_chance_mod /= buff['crit_inc']
			#undo RS
			if buff['skill_name'] == 'Raging Strikes':
				self.dmg_mod /= buff['dmg_inc']

			self.buffs.remove(buff)

		retVal['time'] += timePassed
		return retVal

	#reset GCD timer method
	def gcdUsed(self):
		for i in range(len(self.skillData)):
			if self.skillData[i]['cd'] == 'GCD':
				self.skillData[i]['cd_timer'] = self.GCD_TIME

	def setBloodAndRain(self):
		for i in range(len(self.skillData)):
			if self.skillData[i]['skill_name'] == 'Bloodletter' or self.skillData[i]['skill_name'] == 'Rain of Death':
				self.skillData[i]['cd_timer'] = self.skillData[i]['cd']

	def resetBloodAndRain(self):
		for i in range(len(self.skillData)):
			if self.skillData[i]['skill_name'] == 'Bloodletter' or self.skillData[i]['skill_name'] == 'Rain of Death':
				self.skillData[i]['cd_timer'] = 0

	def IronJawsReset(self):
		for i in range(len(self.dots)):
			if self.dots[i]['skill_name'] == 'Stormbite' or self.dots[i]['skill_name'] == 'Caustic Bite':
				self.dots[i]['dot_timer'] = self.dots[i]['dot_dura']
				self.dots[i]['tick_timer'] = self.TICK_RATE

	def applyBuff(self, skill):
		applied = 0
		for i in range(len(self.buffs)):
			if self.buffs[i]['skill_name'] == skill['skill_name']:
				self.buffs[i]['buff_timer'] = self.buffs[i]['buff_dura']
				applied = 1

		if applied == 0:
			skill['buff_timer'] = skill['buff_dura']
			self.buffs.append(skill)

			if skill['skill_name'] == 'Straight Shot':
				self.crit_chance_mod *= skill['crit_inc']

			if skill['skill_name'] == 'Raging Strikes':
				self.dmg_mod *= skill['dmg_inc']


	#calculate crit and dhit, then return the true potency
	#TODO2: repetoire stacks
	def dealDamage(self,skillUsed):
		
		basePotency = skillUsed['potency']

		potency = basePotency

		#TODO: make these RNG rolls more accurate, good enough for now

		#crit
		rngRoll = random.randint(1,100)
		if rngRoll <= (self.crit_chance * self.crit_chance_mod):
			potency *= self.crit_dmg_mod

		#dhit
		rngRoll = random.randint(1,100)
		if rngRoll <= (self.dhit_chance * self.dhit_chance_mod):
			potency *= self.dhit_dmg_mod

		return potency * self.dmg_mod


'''
SIMULATOR
	-Current iteration: Command line
	-Next: use website for skill entry
	-Final: enable entry for a ML program
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

#parse timer
parse_length = 35000 #ms

while total_time < parse_length:
	useList = sim.getUseableSkills()

	#hacky clear screen
	print(chr(27) + "[2J")

	print 'Potency dealt:', total_potency
	print 'Current dot timings:'
	for dot in sim.dots:
		if dot['skill_name'] != 'auto_attack':
			print dot['skill_name'], ' Timer (s): ', dot['dot_timer'] / 1000

	print '\n'

	print 'Current buff timings:'
	for buff in sim.buffs:
		print buff['skill_name'], ' Timer (s): ', buff['buff_timer'] / 1000

	print '\n'
	print getEntryNames(useList)
	skillName = raw_input('Enter which skill you would like to use: ')

	skillResu = {'time':0,'potency':0}

	if skillName != 'None':
		skillResu = sim.useSkill(skillName)
	else:
		skillResu = sim.doNothing()

	total_potency += skillResu['potency']
	total_time += skillResu['time']


print 'total_potency: ', total_potency
print 'total_time(ms): ', total_time
print 'total PPS: ', total_potency / (total_time / 1000)