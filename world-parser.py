import time, re, os, sys, json
from enum import Enum

std = "DEFAULT"
lineage = "LINEAGE"
precycle = "PRECYCLE"
night = "NIGHT" 

def main():
	args = sys.argv[1:]

	file_path:str = ""
	do_log:bool = False
	scugs = ['White','Yellow','Red','Gourmand','Artificer','Spear','Rivulet','Saint','Inv']

	# parse flags/args
	if len(args) > 0:
		for i, arg in enumerate(args):
			# setup config from args
			if arg[0] == '-':
				# arg pair possible to check for arg
				if (i + 1) < len(args) and args[i+1][0] != '-' and args[i+1][0] != '+':
					if arg == '-file' or arg == '-path' or arg == '-world':
						file_path = args[i+1]
					if arg == '-char' or arg == '-scug' or arg == '-slug':
						scugs = [args[i+1]]
				if arg == '-debug':
					do_log = True
			elif arg[0] == '+':
				if arg[1:] not in scugs:
					scugs.append(arg[1:])

	if file_path == "":
		print("no file path specified")
		return
	try:
		file = open(file_path, 'r')
		spawns_search = re.search("(?<=CREATURES)(.+)(?=END CREATURES)", file.read(), re.DOTALL)
		file.close()

		if spawns_search:
			data = {}
			spawns:str = spawns_search.group(1)
			spawns_data:dict = seperate_creature_lines(spawns.splitlines(), do_log)
			for scug in scugs:
				if scug == "" or scug == None:continue
				data[scug] = get_scug_specific_spawns(scug, spawns_data, do_log)

			json.dump(data, open("parsed.json", "w", encoding="utf-8"), indent=4)
	except FileNotFoundError as e:
		print('file not found')

def get_scug_specific_spawns(scug:str, spawns_data:dict, do_log:bool=False):
	data = {std:[],lineage:[],precycle:[],night:[]}
	token_list = [std,lineage,precycle,night]
	for token in token_list:
		creature_list = []
		for line in spawns_data[token]:
			start_index = 0
			try: start_index = line.index(')') + 1
			except ValueError: 
				if do_log:print('doesn\'t contain end bracket')
			if start_index == 0 or scug in line[:start_index]:
				for creature in line[start_index:].split(', '):
					if creature not in creature_list: creature_list.append(creature)
		data[token] = creature_list
	return data

def seperate_creature_lines(lines:list, do_log:bool=False):
	data = {std:[],lineage:[],precycle:[],night:[]}

	#populate data lines based on type of line
	for line in lines:
		if line != "":
			crline = {std:None,lineage:None,precycle:None,night:None}
			start_index = 0
			try: start_index = line.index(')') + 1
			except ValueError: 
				if do_log:print('doesn\'t contain end bracket')
			line_ = line[start_index:]
			conditional = line[:start_index]
			
			#line is for lineages
			if line_[:line_.index(' ')] == 'LINEAGE':	
				line_ = line_[line_.index(':') + 2:]
				line_ = line_[line_.index(':') + 2:]
				line_ = line_[line_.index(':') + 2:]
				for creature in line_.split(','):
					if creature == None:continue
					creature = creature.strip()

					name = ""
					name_search = re.search('(\w+)-[\d\{\.\}-]+$', creature, re.MULTILINE)
					if name_search:
						name = name_search.group(1)
					elif do_log: print('invalid creature token found: ' + creature)
					if name != 'NONE':
						if crline[lineage] == None:
							crline[lineage] = conditional + name
						else:
							crline[lineage] += ", " + name
			else:
				# for non-Lineage lines
				creatures = line_[line_.index(':') + 2:].split(',')
				for creature in creatures:
					if creature == None:continue
					creature = creature.strip()

					nonstd = re.search("-\{(\D+)\}$", creature, re.MULTILINE)

					# get type for creature token
					token = "error"
					if nonstd == None:token = std
					elif nonstd.group(1) == 'PreCycle':token = precycle
					elif nonstd.group(1) == 'Night':token = night

					# append to respective line
					name = ""
					name_search = re.search('^\d+-(\w+)', creature, re.MULTILINE)
					if name_search:
						name = name_search.group(1)
					elif do_log: print('invalid creature token found: ' + creature)
					if name != 'NONE':
						if crline[token] == None:
							crline[token] = conditional + name
						else:
							crline[token] += ", " + name

			if crline[std] != None: data[std].append(crline[std])
			if crline[lineage] != None: data[lineage].append(crline[lineage])
			if crline[precycle] != None: data[precycle].append(crline[precycle])
			if crline[night] != None: data[night].append(crline[night])
	return data



if __name__ == "__main__":
	main()