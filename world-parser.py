#!/usr/bin/env python3.10
import re, sys, json

std = "DEFAULT"
lineage = "LINEAGE"

def main():
	args = sys.argv[1:]

	world_file_path:str = ""
	map_file_path:str = ""
	do_log:bool = False
	scugs = ['White','Yellow','Red','Gourmand','Artificer','Spear','Rivulet','Saint','Inv']

	# parse flags/args
	if len(args) > 0:
		for i, arg in enumerate(args):
			# setup config from args
			if arg[0] == '-':
				# arg pair possible to check for arg
				if (i + 1) < len(args) and args[i+1][0] != '-' and args[i+1][0] != '+':
					if arg == '-file' or arg == '-path' or arg == '-world' or arg == '-map':
						if re.search('world_\w+.txt$', args[i+1], re.DOTALL | re.MULTILINE):
							world_file_path = args[i+1]
						if re.search('map_\w+.txt$', args[i+1], re.DOTALL | re.MULTILINE):
							map_file_path = args[i+1]
					if arg == '-char' or arg == '-scug' or arg == '-slug':
						scugs = [args[i+1]]
				if arg == '-debug':
					do_log = True
			elif arg[0] == '+':
				if arg[1:] not in scugs:
					scugs.append(arg[1:])
	acronym_search = re.search("world_(\w+?).txt", world_file_path)
	acronym = acronym_search.group(1) if acronym_search else "acronym not found"

	if world_file_path == "":
		print("no file path specified")
		return
	room_subregions = {'list':['NONE']}
	has_subregions = False
	if map_file_path == "":
		if do_log: print("no map file specified")
	else:
		try:
			map_file = open(map_file_path, 'r')
			rooms = map_file.read().splitlines()
			for room in rooms:
				if room == "":continue
				
				room_name = ""
				try: 
					room_name = room[:room.index(':')]
				except ValueError: 
					if do_log:print('room line doesn\'t contain semicolon')
				if room_name in ['','Connection']:continue

				subregion = ""
				try: 
					subregion = room[room.rindex('<') + 1:]
				except ValueError: 
					if do_log:print('room line doesn\'t contain lessthan')
				if subregion != '' and do_log: print(room_name + " : " + subregion)
				if subregion != '' and subregion not in room_subregions['list']: room_subregions['list'].append(subregion)
				room_subregions[room_name.upper().strip()] = (0 if subregion not in room_subregions['list'] else room_subregions['list'].index(subregion))
		except FileNotFoundError as e:
			print(e)
		has_subregions = len(room_subregions['list']) > 0
	try:
		file = open(world_file_path, 'r')
		spawns_search = re.search("(?<=CREATURES)(.+)(?=END CREATURES)", file.read(), re.DOTALL)
		file.close()

		if spawns_search:
			data = {}
			spawns:str = spawns_search.group(1)
			spawns_data:dict = seperate_creature_lines(spawns.splitlines(), do_log, has_subregions, room_subregions)
			for scug in scugs:
				if scug == "" or scug == None:continue
				data[scug] = get_scug_specific_spawns(scug.lower(), spawns_data, do_log, has_subregions, room_subregions)

			json.dump({"acronym":acronym, "spawns":data}, open("parsed.json", "w", encoding="utf-8"), indent=4)
	except FileNotFoundError as e:
		print('file not found')

def get_scug_specific_spawns(scug:str, spawns_data:dict, do_log:bool=False, seperate_into_subregions:bool=False, subregions:dict=None):
	if do_log: print(spawns_data)
	data = {}
	token_list = spawns_data.keys()
	if seperate_into_subregions:
		data['NONE'] = {}
		for sub in subregions['list']:
			data[sub] = {}
	for token in token_list:
		creature_list = []
		if seperate_into_subregions:
			creature_list = {}
			creature_list['NONE'] = []
			for sub in subregions['list']:
				creature_list[sub] = []
		else: data[token] = []
		for line_ in spawns_data[token]:
			line = line_
			subregion = None
			if seperate_into_subregions: 
				line = line_[0]
				subregion = subregions['list'][int(line_[1])]
			start_index = 0
			try: 
				start_index = line.index(')') + 1				
			except ValueError: 
				if do_log:print('doesn\'t contain end bracket')
			cond = line[:start_index][1:-1]
			invert = False
			if cond[:2] == 'X-':
				invert = True
				cond = cond[2:]
				if do_log: print('conditional inverted')
			scugs = [x.lower() for x in cond.split(',')]
			#print("start_index == 0: " + str(start_index == 0))
			#print("(" + scug + " " + ("not " if invert else "") + "in " + str(scugs) + "): " + str((scug in scugs) if not invert else (scug not in scugs)))
			if (start_index == 0) or ((scug in scugs) if not invert else (scug not in scugs)):
				for creature in line[start_index:].split(', '):
					if not seperate_into_subregions:
						if creature not in creature_list: 
							if do_log: print("adding " + creature + " to creature list for " + scug)
							if do_log: print("^ found in following line: " + line)
							creature_list.append(creature)
					elif creature not in creature_list[subregion]: creature_list[subregion].append(creature)
		if not seperate_into_subregions:
			data[token] = creature_list
		else:
			for key in creature_list.keys():
				if len(creature_list[key]) != 0:
					data[key][token] = creature_list[key]
	# clean up structure
	data_out = {}

	for key in data.keys():
		if (type(data[key]) == dict and len(data[key].keys()) != 0 ) or (type(data[key]) == list and len(data[key]) != 0):
			data_out[key] = data[key]
		if seperate_into_subregions:
			for key_ in data[key].keys():
				if len(data[key][key_]) != 0:
					data_out[key][key_] = data[key][key_]
	return data_out

def seperate_creature_lines(lines:list, do_log:bool=False, seperate_into_subregions:bool=False, subregions:dict=None):
	data = {std:[],lineage:[]}

	#populate data lines based on type of line
	for line in lines:
		if line != "" and line[:2] != "//":
			crline = {std:None,lineage:None}
			start_index = 0
			try: start_index = line.index(')') + 1
			except ValueError: 
				if do_log:print('doesn\'t contain end bracket')
			line_:str = line[start_index:]
			conditional = line[:start_index]
			
			if do_log: print(line + " ==> " + conditional + ", " + line_[:line_.index(' ')] + ", " + line_[line_.index(':') + 2:])

			#line is for lineages
			if line_[:line_.index(' ')] == 'LINEAGE':	
				line_ = line_[line_.index(':') + 2:]

				room_name = line_[:line_.index(':') + 2]
				if '}' in room_name: room_name = room_name[room_name.index('}')+1:]
				room_name = room_name.upper().strip()
				subregion_index = 0
				if room_name in subregions.keys():
					subregion_index = subregions[room_name]

				line_ = line_[line_.index(':') + 2:]
				line_ = line_[line_.index(':') + 2:]
				for creature in line_.split(','):
					if creature == None:continue
					creature = creature.strip()

					token = "LINEAGE"

					name = ""
					name_search = re.search('(\w+)-*[\d\{\.\}-]*$', creature, re.MULTILINE)
					if name_search:
						name = name_search.group(1)
					elif do_log: print('invalid creature token found: ' + creature)
					if name != 'NONE':
						if token not in crline.keys(): crline[token] = None
						if crline[token] == None:
							if not seperate_into_subregions: crline[token] = conditional + name
							else: crline[token] = (conditional + name, subregion_index)
						else:
							if not seperate_into_subregions: crline[token] += ", " + name
							else: crline[token] = (crline[token][0] + ", " + name, subregion_index)
			else:
				# for non-Lineage lines
				room_name = line_[:line_.index(':')]
				if '}' in room_name: room_name = room_name[room_name.index('}')+1:]
				room_name = room_name.upper().strip()
				subregion_index = 0
				if room_name in subregions.keys():
					subregion_index = subregions[room_name]

				creatures = line_[line_.index(':') + 2:].split(',')
				for creature in creatures:
					if creature == None:continue
					creature = creature.strip()

					nonstd = re.search("-\{(\D+)\}$", creature, re.MULTILINE)

					# get type for creature token
					token = "error"
					if nonstd == None:token = std
					else: token = nonstd.group(1).lower()

					# append to respective line
					name = ""
					name_search = re.search('^\d+-(\w+)', creature, re.MULTILINE)
					if name_search:
						name = name_search.group(1)
					elif do_log: print('invalid creature token found: ' + creature)
					if name != 'NONE':
						if token not in crline.keys(): crline[token] = None
						if crline[token] == None:
							if not seperate_into_subregions: crline[token] = conditional + name
							else: crline[token] = (conditional + name, subregion_index)
						else:
							if not seperate_into_subregions: crline[token] += ", " + name
							else: crline[token] = (crline[token][0] + ", " + name, subregion_index)
			for key in crline.keys():
				if key not in data.keys(): data[key] = []
				if crline[key] != None: data[key].append(crline[key])
				if do_log: print(str(crline[key]) + "\t\t<"+key+">")
	return data

if __name__ == "__main__":
	main()