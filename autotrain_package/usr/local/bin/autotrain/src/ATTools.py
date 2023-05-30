from time import sleep
from ATShared import *
import os
import scm.params as params

from ATTraining import train

# Tab-autocomplete in input() function
import readline
readline.set_completer_delims(' \t\n=')
readline.parse_and_bind("tab: complete")

def validationSet():
	use_validation = input("Use a validation set? [y]/n: ") or "y"

	if use_validation == "y":
		generate_validation = input("Generate a validation set from training set? [y]/n: ") or "y"
		if generate_validation == "n":
			validation_set = input("Validation set [validation_set.yaml]: ") or "validation_set.yaml"
			verifyFiles([validation_set])
			validation_set = loadFileAsString(validation_set)
		else:
			percent = int(input("Percent to divide the training set [20]: ") or 20)
			validation_set = f"GENERATE_FROM_TRAINING_{percent}"
	else:
		validation_set = "NO_VALIDATION"
	return validation_set

def loadFiles():
	requieredFiles = """================
FILE IMPORTER
================
Provide the path for the following files or press enter for [default]:\n
- Initial force field\n
- Job collection\n
- Job engines\n
- Training set\n
- Validation set (optional)\n"""
	print(requieredFiles)

	initialff = input("Initial force field [initial.ff]: ") or "initial.ff"
	jobcol = input("Job collection [job_collection.yaml]: ") or "job_collection.yaml"
	joben = input("Job engines [job_collection_engines.yaml]: ") or "job_collection_engines.yaml"
	training_set = input("Training set [training_set.yaml]: ") or "training_set.yaml"

	files = [initialff, jobcol, joben, training_set]

	verifyFiles(files)

	validation_set = validationSet()

	reqFiles = RequiredFiles()
	reqFiles.initialff = loadFileAsString(initialff)
	reqFiles.jobcol = loadFileAsString(jobcol)
	reqFiles.joben = loadFileAsString(joben)
	reqFiles.training_set = loadFileAsString(training_set)
	reqFiles.validation_set = validation_set

	interface = params.ReaxFFParameters(initialff)

	return reqFiles, interface

def optimizerConfig():
	cmaes="""\n====================
CONFIGURE OPTIMIZER
====================
AutoTrain currently only supports CMA-ES optimizer, as its the most efficient algorithm for optimizing large number of variables. The optimizer requires:
- Sigma
- Minimum sigma
- Population size
- Max steps
- Patience (max number of iterations without the force field improving)
- Loss function [sse, sae, mae, rmse]
- Number of optimizations (times that the whole optimization process is going to be run in a loop)
"""
	print(cmaes)

	opt = OptimizerConf()

	opt.sigma = float(input("Sigma [0.2]: ") or 0.2)
	opt.minsigma = float(input("Minimum sigma [1e-4]: ") or 1e-4) 
	opt.popsize = int(input("Population size [15]: ") or 15)
	opt.maxstep = int(input("Max step [1000]: ") or 1000)
	opt.patience = int(input("Patience [500]: ") or 500)
	opt.loss = input("Loss function [rmse]: ") or "rmse"
	opt.iterations = int(input("Number of iterations [5]: ") or 5)

	return opt

def paramConfig(interface: params.ReaxFFParameters):

	configInfo = """=======================
PARAMETER CONFIGURATION
=======================
"""
	print(configInfo)

	allAtoms = []
	blocks = []
	categos = []
	for param in interface:
		for atom in param.atoms:
			if not atom in allAtoms:
				allAtoms.append(atom)
		if not param.block in blocks:
			blocks.append(param.block)
		if not param.metadata.category in categos:
			categos.append(param.metadata.category)

	print(f"{len(allAtoms)} atoms:")
	for atom in allAtoms:
		print(f"{atom}", end = " ")

	selectAtoms = "\n\nEnter, separated by spaces, the atoms you want to parametrize (default: all):\n"
	selectedAtoms = input(selectAtoms) or " ".join(allAtoms)

	splitAtoms = selectedAtoms.split(" ")
	
	if not checkIfInList(allAtoms, splitAtoms):
		tools()

	atoms = splitAtoms

	selectAvoidAtoms = "\n\nEnter, separated by spaces, the atoms you want to avoid during the parametrization: (default: avoid all not previously selected)\n"
	selectedAvoidAtoms = input(selectAvoidAtoms) or "ALL"

	if selectedAvoidAtoms == "ALL":
		splitAvoidAtoms = []
		for atom in allAtoms:
			if not atom in atoms:
				splitAvoidAtoms.append(atom)
	else:
		splitAvoidAtoms = selectedAvoidAtoms.split(" ")
	
		if not checkIfInList(allAtoms, splitAvoidAtoms):
			tools()
	
		for avoidAtom in splitAvoidAtoms:
			if avoidAtom in atoms:
				print(f"{avoidAtom} was selected for optimization. Aborting.")
				sleep(2)
				tools()

	avoidAtoms = splitAvoidAtoms

	allowRepeated = "\nAllow repeated atom in parameter? For example: Fe-Fe, O-O, H-O-H... [Y]/n\n"
	allowRepeated = input(allowRepeated)

	if allowRepeated == "N" or allowRepeated == "n":
		allowRepeated = 0
	else: 
		allowRepeated = 1
	
	print(f"\n{len(blocks)} blocks:")
	for block in blocks:
		print(f"{block}", end = " ")

	selectBlocks = "\n\nEnter, separated by spaces, the blocks you want to parametrize:\n"
	selectedBlocks = input(selectBlocks) or "NULL"

	splitBlocks = selectedBlocks.split(" ")

	if not checkIfInList(blocks, splitBlocks):
		tools()
	
	blocks = splitBlocks

	print(f"\n{len(categos)} categories:")
	for catego in categos:
		print(f"{catego}", end = " ")

	selectCatego = "\n\nEnter, separated by spaces, the categories you want to parametrize:\n"
	selectedCatego = input(selectCatego) or "NULL"

	splitCategos = selectedCatego.split(" ")

	if not checkIfInList(categos, splitCategos):
		tools()
	
	categos = splitCategos

	availableTechniques="""
There are four predefined optimization techniques:
[1] Random parameter activation
[2] By atoms (optimize all parameters of each atom at a time)
[3] By blocks (optimize a full block at a time)
[4] By categories (optimize a single category at a time)
[5] All at once
"""

	selectOptimizationTechnique = input(availableTechniques) or "0"

	try:
		optT = int(selectOptimizationTechnique)
	except:
		print("Error selecting optimization technique. Aborting.\n")
		sleep(2)
		tools()

	if optT > 5 or optT < 1:
		print(f"Technique {optT} does not exist. Aborting.\n")
		sleep(2)
		tools()
	
	pRound = 0
	if optT == 1:
		paramsPerRound = input("How many parameters to optimize each round? (minimum 3): ") or "3"
		try:
			pRound = int(paramsPerRound)
		except:
			print("Error selecting parameters per round. Aborting.\n")
			sleep(2)
			tools()
		if pRound < 3:
			print(f"Minimum parameters per round is 3. Aborting.\n")
			sleep(2)
			tools()

	pInterface = ParamInterface()
	pInterface.allowRepeated = allowRepeated
	pInterface.atoms = atoms
	pInterface.avoidAtoms = avoidAtoms
	pInterface.blocks = blocks
	pInterface.categos = categos
	pInterface.optTechnique = selectOptimizationTechnique
	pInterface.paramsPerRound = pRound

	return pInterface

def editParamConfig(loadedJSON):

	ffield = loadedJSON["files"]["initialff"]

	tmp = tempFile("ffieldtmp", ffield)

	paramInfo="This tool can help you setting to active bluk parameters based upon atom type, block type or param category. For a more refined confgiuration, activate the parameters using ParAMS"
	print(paramInfo)
	interface = params.ReaxFFParameters(tmp.fileName)
	tmp.destroy()
	pInterface = paramConfig(interface=interface)

	loadedJSON["parameterInterface"] = interfaceToJSON(pInterface)
	saveJSONToFile(loadedJSON["name"], loadedJSON)

def generateAutoTrainJSON():

	files, interface = loadFiles()
	optconf = optimizerConfig()
	configuredInterface = paramConfig(interface=interface)
	name = input("Give this configuration a name [autotrain]: ") or "autotrain"

	trainConfig = TrainConfiguration()
	trainConfig.name = name
	trainConfig.optConf = optconf
	trainConfig.parameterInterface = configuredInterface
	trainConfig.data = files


	writeJSON(trainConfig=trainConfig)
	
	import AutoTraining
	AutoTraining.selectSubprogram()

def editName(loadedJSON):
	newName = input("Enter new name: ") or "autotrain"
	loadedJSON["name"] = newName
	saveJSONToFile(newName, loadedJSON)

def printCurrentOptimizer(opt):
	currentConfigDisplay = f"""Current configuration:
====================
Sigma: {opt["sigma"]}
Minsigma: {opt["minsigma"]}
Popsize: {opt["popsize"]}
Maxstep: {opt["maxstep"]}
Patience: {opt["patience"]}
Loss: {opt["loss"]}
Iterations: {opt["iterations"]}
====================
"""
	print(currentConfigDisplay)

def editOptimizer(loadedJSON):
	config = loadedJSON["optimizer"]
	printCurrentOptimizer(config)
	newConfig = optimizerConfig()
	loadedJSON["optimizer"] = optimizerToJSON(newConfig)
	saveJSONToFile(loadedJSON["name"], loadedJSON)

def editFiles(loadedJSON):
	reqFiles = loadedJSON["files"]
	editInfo = """Select a file to update:
[1] Initial ForceField
[2] Job Collection
[3] Job Engines
[4] Training set
[5] Validation set
[Other] Go back
"""
	print(editInfo)
	choice = input() or "0"

	validChoices = ["1", "2", "3", "4", "5"]

	if not choice in validChoices:
		tools()

	if choice != "5":
		newFile = input("Enter new file: ")
		verifyFiles([newFile])

	if choice == "1":
		reqFiles["initialff"] = loadFileAsString(newFile)
	elif choice == "2":
		reqFiles["jobcol"] = loadFileAsString(newFile)
	elif choice == "3":
		reqFiles["joben"] = loadFileAsString(newFile)
	elif choice == "4":
		reqFiles["training_set"] = loadFileAsString(newFile)
	elif choice == "5":
		reqFiles["validation_set"] = validationSet()
	loadedJSON["files"] = reqFiles
	saveJSONToFile(loadedJSON["name"], loadedJSON)
	tools()

def editAutoTrainJSON():
	file = input("Enter file to edit: [autotrain.json] ") or "autotrain.json"
	verifyFiles([file])
	loaded = loadJSON(file)

	chooseEdit = """Edit:
[1] Name
[2] Optimizer settings
[3] Required files
[4] Parameter config
[Other] Go back
"""

	option = input(chooseEdit) or "0"
	os.system("clear")
	if option == "1":
		editName(loaded)
	if option == "2":
		editOptimizer(loaded)
	if option == "3":
		editFiles(loaded)
	if option == "4":
		editParamConfig(loaded)
	
	tools()

# Add reactants or products to the training set. Returns the energy, and the corresponding expression
def addToTraining(type: str, jobcollection: params.JobCollection):
	from scm.plams import Molecule
	addEntries = True
	expression = ""
	toten = 0
	currentE = 0
	print(f"Enter {type}: ")
	while (addEntries):
		entryName = input("Name of the entry: ")
		if entryName in jobcollection:
			print("Entry already exists. Reusing geometry and energy data")
			currentE = jobcollection[entryName].metadata["energy"]
		else:
			geofile = input("Enter xyz file: ") 
			verifyFiles([geofile])
			jce = params.JCEntry()
			jce.settings.input.AMS.Task = 'SinglePoint'
			jce.molecule = Molecule(geofile)
			currentE = float(input("Energy (eV): ") or 0)
			jce.metadata["energy"] = currentE
			jobcollection.add_entry(entryName,jce)
		sto = float(input("Stoichiometry [1.0]: ") or 1.0)
		if type == "Reactants": 
			expression += f"""-{sto}*energy("{entryName}")"""
		if type == "Products":
			expression += f"""+{sto}*energy("{entryName}")"""
		toten += sto*currentE
		addNewEntry = input(f"Add new {type}? [y]/n ") or "y"
		if addNewEntry == "n":
			addEntries = False
	return toten, expression

def addEnergies(toTraining: str, tojc: str):
	ds = params.DataSet(toTraining)
	jc = params.JobCollection(tojc)

	description = """This tool will ask for the structures and their energies. First the reactants and then the products, thus the resulting energy is products-reactants
"""
	print(description)
	addEntries = True
	while (addEntries):

		reacts, expressionReact = addToTraining("Reactants", jc)
		print("")
		prods, expressionProd = addToTraining("Products", jc)
		print("")
		expression = expressionProd + expressionReact
		energy = prods - reacts

		weight = float(input("Weight of the entry [1.0]: ") or 1.0)
		sigma = float(input("Sigma [0.54422]:") or 0.05442279126360184)

		ds.add_entry(expression,
					weight=weight,
					reference=energy,
					unit=('eV', 27.21139563180092),
					sigma=sigma)

		jc.store("job_collection.yaml")
		ds.store("training_set.yaml")		
		added = f"""======Added======
Expression: {expression}
Weight: {weight}
Sigma: {sigma}
ReferenceValue: {energy}
Unit: eV, 27.21139563180092
================="""
		print(added)
		addn = input("Add new expression? [y]/n: ") or "y"
		if addn == "n":
			addEntries = False
	print("Finished adding expressions and saved files")
	input("Press any key to continue...")
	tools()

def addForces(trainfile, jobcol):
	import scm
	os.system("clear")
	description = "This tool will add reference values for forces to selected atoms\n"
	print(description)
	ds = params.DataSet(trainfile)
	jobcollection = params.JobCollection(jobcol)
	addEntries = True
	while (addEntries):
		entryName = input("Name of the entry: ")
		if entryName in jobcollection:
			print(f"{entryName} already exists. Reusing geometry data")
			molecule = jobcollection[entryName].molecule
		else:
			geofile = input("Enter xyz file: ") 
			verifyFiles([geofile])
			jce = params.JCEntry()
			jce.settings.input.AMS.Task = 'SinglePoint'
			molecule = scm.plams.Molecule(geofile)
			jce.molecule = molecule
			jobcollection.add_entry(entryName,jce)

		sigma = float(input("Sigma [0.1542]:") or 0.1542662024289777)
		atoms = len(molecule.atoms)

		setforce = float(input("Value to set forces to [0]: ") or "0")
		enableatoms = input(f"Enable atoms from {1} to {atoms} separated by spaces or negative (-X) to count a range from the last atom to last-X. For example, when having 200 atoms, specifying -5 will enable atoms 196, 197, 198, 199 and 200").split(" ")
		components = ["x", "y", "z"]
		enable = ""
		if int(enableatoms[0]) < 0:
			for i in range(abs(int(enableatoms[0]))):
				enable += f"{atoms-i} "
			enable = enable.split(" ")
			enable.pop()
		else:
			enable = enableatoms
		for e in enable:
			print(f"Set atom {e} ({molecule[int(e)].symbol}) forces to {setforce} in {entryName}")
			expression = f'forces("{entryName}", atindex={int(e)-1})'
			values = []
			for c in components:
				values.append(setforce)
			ds.add_entry(expression,
					reference=values,
					unit=("eV/Angstrom", 51.422067476325886),
					sigma=sigma)

		jobcollection.store("job_collection.yaml")
		ds.store("training_set.yaml")		
		addn = input("Add new expression? [y]/n: ") or "y"
		if addn == "n":
			addEntries = False
	print("Finished adding forces and saved files")
	input("Press any key to continue...")
	tools()


def trainingSetEditor():
	description = """Edit a training set:
[1] Add Energies
[2] Add Forces
[Other] Exit
"""
	print(description)

	choice = input("") or "-1"
	if choice == "1":
		trainfile = input("Enter training set file [training_set.yaml]: ") or "training_set.yaml"
		jcfile = input("Enter job collection file [job_collection.yaml]: ") or "job_collection.yaml"
		verifyFiles([trainfile, jcfile])
		addEnergies(trainfile, jcfile)
	elif choice == "2":
		trainfile = input("Enter training set file [training_set.yaml]: ") or "training_set.yaml"
		jcfile = input("Enter job collection file [job_collection.yaml]: ") or "job_collection.yaml"
		verifyFiles([trainfile, jcfile])
		addForces(trainfile, jcfile)
	else:
		tools()


def fileExtractor():
	description="""This tool extracts the training info from an autotrain.json file. The output files are:
initial.ff
training_set.yaml
validation_set.yaml (if any)
job_collection.yaml
job_collection_engines.yaml
"""
	print(description)
	file = input("Enter file: ")

	import ATShared

	if not ATShared.verifyFiles([file]):
		tools()
	
	configuration = ATShared.loadJSONIntoTrainConfiguration(file)
	print("Extracting initial force field set...")
	initialff = ATShared.tempFile("initial.ff", configuration.data.initialff)
	print("Extracting training set...")
	training_set = ATShared.tempFile("training_set.yaml", configuration.data.training_set)
	print("Extracting validation set...")
	validation_set = ATShared.tempFile("validation_set.yaml", configuration.data.validation_set)
	print("Extracting job collection...")
	job_collection = ATShared.tempFile("job_collection.yaml", configuration.data.jobcol)
	print("Extracting job collection engines...")
	job_collection_engines = ATShared.tempFile("job_collection_engines.yaml", configuration.data.joben)
	print("Files sucessfully extracted\n")
	sleep(1)
	tools()

def vaspConverter():
	import vaspConverter
	description = """This tool will convert recursively all the CONTCAR and POSCAR files found inside the defined folder.
Tool provided by Lenard Carroll in https://github.com/lenardcarroll/POSCARtoXYZ"""
	print(description)

	folder = input("Start folder X: ")
	#verifyFiles([folder])

	t = 0
	n = 0
	print("Searching contcars...\n")
	for root, dirs, files in os.walk(folder):
		# Prefer contcar over poscar
		didContcar = False
		for file in files:
			if file == "CONTCAR" :
				print(f"Converting: {os.path.join(root, file)}")
				t += 1
				try: 
					vaspConverter.fracpos2xyz(os.path.join(root, file))
					n += 1
				except:
					print(f"Error converting {os.path.join(root, file)} with fractional coords. Retrying with direct coords...")
					try:
						vaspConverter.pos2xyz(os.path.join(root, file))
						print(f"Converted!")
						n += 1
					except:
						print("Error converting file... Skipping")
						continue
				didContcar = True
		if not didContcar:
			for file in files:
				if file == "POSCAR" :
					t += 1
					print(f"Converting: {os.path.join(root, file)}")
					try: 
						vaspConverter.fracpos2xyz(os.path.join(root, file))
						n += 1
					except:
						print(f"Error converting {os.path.join(root, file)} with fractional coords. Retrying with direct coords...")
						try:
							vaspConverter.pos2xyz(os.path.join(root, file))
							n += 1
							print(f"Converted!")
						except:
							print("Error converting file... Skipping")
							continue

	input(f"Converted {n}/{t} files. Press any key to continue...")
	tools()

# This function writes the reference data along the predicted data on the best force field for plotting purposes
# Returns the header and the data ready to be written into a csv file
def computePredictions(engine: params.Engine, jobcol: params.DataSet, data_set: params.DataSet):
	dse = params.DataSetEvaluator(data_set)
	print("Calculating predicted values...")
	dse.run(jobcol, data_set, engine)
	dse.group_by(('Extractor', 'Expression'))
	predictions = dse.results["energy"].predictions
	reference = dse.results["energy"].reference_values
	expression = dse.results["energy"].expressions
	header = ["expression","reference","prediction"]
	data = []
	for i in range(len(expression)):
		data.append([expression[i], reference[i], predictions[i]])
	return header, data

def csvWritter(header, data, name="predictions.csv"):
	print("Writting csv...")
	import csv
	with open(name, 'w', encoding='UTF8', newline='') as f:
		writer = csv.writer(f)
		# Write the header
		writer.writerow(header)
		# Write the data
		writer.writerows(data)
		

def predictionTool():
	import ATShared
	json = input("Autotrain .json: ")
	verifyFiles([json])
	loaded_json = ATShared.loadJSONIntoTrainConfiguration(json)
	ffield = input("Forcefield to evaluate (blank to use the one provided in the json file) ") or "NULL"
	print("Loading files...")
	if ffield == "NULL":
		tmp = tempFile("tmp_ffield", loaded_json.data.initialff)
		reaxFF = params.ReaxFFParameters(tmp.fileName)
		tmp.destroy()
	else:
		reaxFF = params.ReaxFFParameters(ffield)

	tmpjobcol = tempFile("tmp_jobcol", loaded_json.data.jobcol)
	jobcol = params.JobCollection(tmpjobcol.fileName)
	tmpjobcol.destroy()

	tmptrainset = tempFile("tmp_trainset", loaded_json.data.training_set)
	trainset = params.DataSet(tmptrainset.fileName)
	tmptrainset.destroy()

	header, data = computePredictions(reaxFF, jobcol, trainset)
	csvWritter(header, data)

def parameterList():
	import ATTraining
	import ATShared

	description = "Print a set of parameter properties with ease from an autotrain.json file."
	print(description)

	configurationFile = input("Load training configuration file [autotrain.json]: ") or "autotrain.json"
	ATShared.verifyFiles([configurationFile])
	configuration = ATShared.loadJSONIntoTrainConfiguration(configurationFile)

	tmp = ATShared.tempFile("ffieldtmp", configuration.data.initialff)
	interface = params.ReaxFFParameters(tmp.fileName)
	tmp.destroy()

	wantedParams = ATTraining.getAllWantedParams(interface=interface, interConf=configuration.parameterInterface)
	print("==========Configuration==========")
	print(f"Wanted atoms: {' '.join(configuration.parameterInterface.atoms)}")
	print(f"Avoiding: {' '.join(configuration.parameterInterface.avoidAtoms)}")
	print(f"Blocks: {' '.join(configuration.parameterInterface.blocks)}")
	print(f"Categories: {' '.join(configuration.parameterInterface.categos)}")
	print(f"Allow repeated: {bool(configuration.parameterInterface.allowRepeated)}")
	print(f"Wanted parameters: {len(wantedParams)}")
	print("===========Parameters============")
	row = ["Name", "Value", "Atoms", "Block", "Category"]
	print("{: >20}\t{: >20}\t{: >20}\t{: >20}\t{: >20}".format(*row))
	for param in wantedParams:
		joinedAtoms = "-".join(param.atoms)
		row = [param.name, param.value, joinedAtoms, param.block, param.metadata.category]
		print("{: >20}\t{: >20}\t{: >20}\t{: >20}\t{: >20}".format(*row))
	input("Press any key to continue...")

def jobColList():
	import ATTraining
	import ATShared

	description = "Prints the job collection IDs from an autotrain.json file."
	print(description)

	configurationFile = input("Load training configuration file [autotrain.json]: ") or "autotrain.json"
	ATShared.verifyFiles([configurationFile])
	configuration = ATShared.loadJSONIntoTrainConfiguration(configurationFile)

	tmp = ATShared.tempFile("jobcoltmp", configuration.data.jobcol)
	jc = params.JobCollection(tmp.fileName)
	tmp.destroy()

	for j in jc:
		print(j)

	input("Press any key to continue...")

def computeOptimizations(engine: params.Engine, jobcol: params.DataSet, data_set: params.DataSet):

	ts_engine = engine.get_engine()
	ts_settings = ts_engine.settings
	ts_engine.settings = ts_settings

	opt_engine = engine.get_engine()
	opt_settings = opt_engine.settings
	opt_settings.input.ReaxFF.TaperBO = 'Yes'
	opt_settings.input.ReaxFF.Torsions = '2013'
	opt_settings.input.ReaxFF.Charges.DisableChecks = 'Yes'
	opt_settings.input.ReaxFF.NonReactive = 'Yes'
	opt_engine.settings = opt_settings

	ec = params.EngineCollection()
	ec.add_entry('minima', opt_engine)
	ec.add_entry('ts', ts_engine)
	
	print("Tasks:")
	new_jc = params.JobCollection()
	# minima_jc = params.JobCollection()
	# ts_jc = params.JobCollection()
	# has_minima = False
	# has_ts = False
	for j in jobcol:
		jce = jobcol[j]
		if 'TS' in j:
			#has_ts = True
			jce.settings.input.AMS.Task = 'TransitionStateSearch'
			jce.reference_engine = 'ts'
			#ts_jc.add_entry(j, jce)
			new_jc.add_entry(j, jce)
		else:
			#has_minima = True
			jce.settings.input.AMS.Task = 'GeometryOptimization'
			jce.reference_engine = 'minima'
			#minima_jc.add_entry(j, jce)
			new_jc.add_entry(j, jce)

	dse = params.DataSetEvaluator()
	print("Evaluating data set...")
	dse.calculate_reference(new_jc, data_set, ec, overwrite=True, folder='optimization_results')

	# if has_minima:
	# 	print("Evaluating data set...")
	# 	dse.run(minima_jc, data_set, opt_engine.settings, folder='optimization_results')

	# if has_ts:
	# 	print("Evaluating data set...")
	# 	dse.run(ts_jc, data_set, ts_engine.settings, folder='optimization_results')

	print("Finished...")

def optimizeStructures():
	import ATShared
	
	description = "Optimize the structures present in autotrain.json with a given forcefield"
	print(description)

	json = input("Autotrain .json: ")
	verifyFiles([json])
	loaded_json = ATShared.loadJSONIntoTrainConfiguration(json)
	ffield = input("Forcefield to evaluate (blank to use the one provided in the json file) ") or "NULL"
	print("Loading files...")
	if ffield == "NULL":
		tmp = tempFile("tmp_ffield", loaded_json.data.initialff)
		reaxFF = params.ReaxFFParameters(tmp.fileName)
		tmp.destroy()
	else:
		reaxFF = params.ReaxFFParameters(ffield)

	tmpjobcol = tempFile("tmp_jobcol", loaded_json.data.jobcol)
	jobcol = params.JobCollection(tmpjobcol.fileName)
	tmpjobcol.destroy()

	tmptrainset = tempFile("tmp_trainset", loaded_json.data.training_set)
	trainset = params.DataSet(tmptrainset.fileName)
	tmptrainset.destroy()

	#header, data = computeOptimizations(reaxFF, jobcol, trainset)
	#csvWritter(header, data, name="optimizations.csv")
	computeOptimizations(reaxFF, jobcol, trainset)


def tools():
	available_tools = """[1] AutoTrain.json generator
[2] AutoTrain.json editor
[3] Training set editor
[4] File extractor
[5] VASP to XYZ
[6] CSV reference vs. prediction
[7] Wanted parameters list
[8] Job collection list
[9] Optimize structures
[Other] Go back
"""
	os.system("clear")
	print(available_tools)
	tool = input("Select tool: ") or "0"

	if tool == "1":
		os.system("clear")
		generateAutoTrainJSON()
	if tool == "2":
		os.system("clear")
		editAutoTrainJSON()
	if tool == "3":
		os.system("clear")
		trainingSetEditor()
	if tool == "4":
		os.system("clear")
		fileExtractor()
	if tool == "5":
		os.system("clear")
		vaspConverter()
	if tool == "6":
		os.system("clear")
		predictionTool()
	if tool == "7":
		os.system("clear")
		parameterList()
	if tool == "8":
		os.system("clear")
		jobColList()
	if tool == "9":
		os.system("clear")
		optimizeStructures()

	else:
		import AutoTraining
		AutoTraining.selectSubprogram()