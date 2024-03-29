from audioop import add
import json
from tabnanny import verbose
import scm.params as pms
import ATShared
from time import sleep
import time
import random
import sys
import csv


def printTime(msg: str = ""):
	t = time.localtime()
	current_time = time.strftime("%Y-%m-%d %H:%M:%S", t)
	print(f"{msg} {current_time}")

def train(jsonAsARG: str = "NULL"):

	autotrainInfo = """Autotrain. ParAMS configurator and optimizer.
Christian Domínguez
https://github.com/chdominguez/ParAMSAutoTrain
""" 
	print(autotrainInfo)
	
	printTime("Started at")

	if jsonAsARG != "NULL":
		if not ATShared.verifyFiles([jsonAsARG], abort=False):
			print(f"\nError, input file {jsonAsARG} does not exist.\n")
			printTime("Finished at")
			sys.exit(1)
		configuration = ATShared.loadJSONIntoTrainConfiguration(jsonAsARG)
	else:
		configurationFile = input("Load training configuration file [autotrain.json]: ") or "autotrain.json"
		ATShared.verifyFiles([configurationFile])
		configuration = ATShared.loadJSONIntoTrainConfiguration(configurationFile)

	print("Loading configuration\n")

	tmp = ATShared.tempFile("ffieldtmp", configuration.data.initialff)
	interface = pms.ReaxFFParameters(tmp.fileName)
	tmp.destroy()

	print("Wanted parameters: ")
	wantedParams = getAllWantedParams(interface=interface, interConf=configuration.parameterInterface)
	print("==========Configuration==========")
	print(f"Wanted atoms: {' '.join(configuration.parameterInterface.atoms)}")
	print(f"Avoiding: {' '.join(configuration.parameterInterface.avoidAtoms)}")
	print(f"Blocks: {' '.join(configuration.parameterInterface.blocks)}")
	print(f"Categories: {' '.join(configuration.parameterInterface.categos)}")
	print(f"Wanted parameters: {len(wantedParams)}")
	print("===========Parameters============")
	row = ["Name", "Value", "Atoms", "Block", "Category"]
	print("{: >20}\t{: >20}\t{: >20}\t{: >20}\t{: >20}".format(*row))
	for param in wantedParams:
		joinedAtoms = "-".join(param.atoms)
		row = [param.name, param.value, joinedAtoms, param.block, param.metadata.category]
		print("{: >20}\t{: >20}\t{: >20}\t{: >20}\t{: >20}".format(*row))

	if configuration.parameterInterface.optTechnique == "1":
		blocks = randomParamsBlocks(configuration.parameterInterface.paramsPerRound, wantedParams)
		print("\nUsing random parameters techinque\n")
	elif configuration.parameterInterface.optTechnique == "2":
		blocks = atomParamsBlock(configuration.parameterInterface.atoms, wantedParams)
		print("\nOptimizing by atoms\n")
	elif configuration.parameterInterface.optTechnique == "3":
		blocks = blockParams(configuration.parameterInterface.blocks, wantedParams)
		print("\nOptimizing by blocks\n")
	elif configuration.parameterInterface.optTechnique == "4":
		blocks = categoParamsBlocks(configuration.parameterInterface.categos, wantedParams)
		print("\nOptimizing by categories\n")
	elif configuration.parameterInterface.optTechnique == "5":
		blocks = [wantedParams]
		print("\nOptimizing all at once\n")
	else:
		print("\nNo technique was specified, using random parameters:\n")
		sleep(1)
		blocks = randomParamsBlocks(configuration.parameterInterface.paramsPerRound, wantedParams)
	
	print(f"Start optimizing {configuration.name}\n")
	optimize(configuration, blocks, interface)

def generateValidation(data_set: pms.DataSet, percent):
	perOne = percent/100
	training, validation = data_set.split(1-perOne, perOne)
	return training, validation

def loadValidation(validationString: str):
	tmpValidation = ATShared.tempFile("validation", validationString)
	validation_set = pms.DataSet(tmpValidation.fileName)
	tmpValidation.destroy()
	return validation_set

def setupCallbacks(configuration: ATShared.TrainConfiguration):
	max = pms.MaxIter(configuration.optConf.maxstep, verbose=True)
	patience = pms.EarlyStopping(patience=configuration.optConf.patience, watch='training_set', verbose=True)
	return [max, patience]

def setupLogger(name):
	logger = pms.Logger(path=f'../{name}.log', every_n_iter=10, group_by=None, iteration_digits=6, sort_stats_by='contribution')
	return logger
	
def optimize(configuration: ATShared.TrainConfiguration, blocks, interface):

	jobcoltmp = ATShared.tempFile("jobcol", configuration.data.jobcol)
	joben = ATShared.tempFile("job_collection_engines.yaml", configuration.data.joben)
	jc = pms.JobCollection(jobcoltmp.fileName)
	jobcoltmp.destroy()
	joben.destroy()

	trainsettmp = ATShared.tempFile("trainset", configuration.data.training_set)
	data_set = pms.DataSet(trainsettmp.fileName)
	trainsettmp.destroy()
	
	data_sets =[] 

	if "GENERATE_FROM_TRAINING_" in configuration.data.validation_set:
		training_set, validation_set = generateValidation()
		data_set.append(training_set)
		data_set.append(validation_set)
	elif configuration.data.validation_set != "NO_VALIDATION":
		validation_set = loadValidation(configuration.data.validation_set)
		data_set.append(data_set)
		data_set.append(validation_set)
	else:
		data_sets = [data_set]

	callbacks = setupCallbacks(configuration)
	parallel = pms.ParallelLevels(parametervectors=8, jobs=1)

	bestffield = ""

	if ATShared.verifyFiles(["restart.at.json"], abort=False):
		restart = ATShared.loadJSON("restart.at.json")
		print("Restarting optimization from restart file.")
		checkpoint = True
	else:
		checkpoint = False    

	iterations = int(configuration.optConf.iterations)

	if checkpoint:
		iterations = int(restart["iterations_left"])
		bestffield = restart["bestffield"]
		lastBlock = int(restart["lastblock_index"])
		print(f"Iterations left: {iterations}")
		print(f"Best forcefield: {bestffield}")
		print(f"Last block index: {lastBlock}\n")

	for i in range(iterations):
		for p in range(len(blocks)):
			if checkpoint:
				if p == lastBlock:
					checkpoint = False
				else:
					continue
			if bestffield != "":
				interface = pms.ReaxFFParameters(bestffield)
			active = activate(blocks[p], interface)
			optimizer    = pms.CMAOptimizer(popsize=configuration.optConf.popsize, sigma=configuration.optConf.sigma, minsigma=configuration.optConf.minsigma)
			#optimization = pms.Optimization(jc, data_sets, active, optimizer, parallel=parallel, loss=configuration.optConf.loss, callbacks=callbacks)
			optimization = pms.Optimization(jc, data_sets, active, optimizer, loss=configuration.optConf.loss, callbacks=callbacks)
			optimization.optimize()
			optimization.summary()
			bestffield = optimization.workdir + "/training_set_results/best/ffield.ff"

			restart = ATShared.Restart
			restart.bestffield = bestffield
			restart.iterations_left = iterations - i - 1
			if p + 1 == len(blocks):
				restart.lastblock_index = 0
			else:
				restart.lastblock_index = p + 1

			ATShared.writeRestartJSON(restart)
			import ATTools
			# Save predictions
			for i in range(len(data_sets)):
				header, data = ATTools.computePredictions(active, jc, data_sets[i])
				name = "training_set_predictions.csv"
				if i == 1:
					name = "validation_set_predictions.csv"
				ATTools.csvWritter(header, data, name)

	print("\nNormal AutoTrain termination")

	# Finished optimization, save final.ff
	bestFile = ATShared.loadFileAsString(bestffield)
	with open("final.ff", 'w') as f:
		f.write(bestFile)

	print("Saved best forcefield as final.ff")

	printTime("Finished at")

def activate(params, interface):
	for p in interface:
		for pp in params:
			if p.name == pp.name:
				p.is_active = True
	return interface

def checkIfDuplicates(listOfElems):
    ''' Check if given list contains any duplicates '''
    if len(listOfElems) == len(set(listOfElems)):
        return False
    else:
        return True

def getAllWantedParams(interface: pms.ReaxFFParameters, interConf: ATShared.ParamInterface):
	wantedParams = []
	for param in interface:
		complyAtoms = False
		complyCatego = False
		complyBlock = False

		if len([i for i in interConf.atoms if i in param.atoms]) > 0:
			if len([i for i in interConf.avoidAtoms if i in param.atoms]) == 0:
				if bool(interConf.allowRepeated):
					complyAtoms = True
				else:
					if not checkIfDuplicates(param.atoms):
						complyAtoms = True
		if param.block in interConf.blocks:
			complyBlock = True
			if param.block == "GEN":
				complyAtoms = True
				complyCatego = True
		if param.metadata.category in interConf.categos:
			complyCatego = True
		if complyAtoms and complyBlock and complyCatego:
			wantedParams.append(param)

	return wantedParams

def randomParamsBlocks(paramsPerRound, wantedParams):
	paramsPerRound = int(paramsPerRound)
	random.shuffle(wantedParams)
	countingParams = wantedParams
	paramBlocks = []
	while len(countingParams) >= paramsPerRound:
		prand = countingParams[:paramsPerRound]
		paramBlocks.append(prand)
		countingParams = countingParams[paramsPerRound:]
	if len(countingParams) != 0:
		prand = countingParams
		paramBlocks.append(prand)
	return paramBlocks

def atomParamsBlock(wantedAtoms, wantedParams):
	paramBlocks = []
	for wa in wantedAtoms:
		b = []
		for p in wantedParams:
			if wa in p.atoms:
				b.append(p)
		if len(b) > 0:
			paramBlocks.append(b)
	return paramBlocks 

def blockParams(wantedBlocks, wantedParams):
	paramBlocks = []
	for wblock in wantedBlocks:
		b = []
		for p in wantedParams:
			if p.block == wblock:
				b.append(p)
		if len(b) > 0:
			paramBlocks.append(b)
	return paramBlocks	

def categoParamsBlocks(wantedCategos, wantedParams):
	paramBlocks = []
	for wcatego in wantedCategos:
		b = []
		for p in wantedParams:
			if wcatego == p.metadata.category:
				b.append(p)
		if len(b) > 0:
			paramBlocks.append(b)
	return paramBlocks

def setupOptimizerCallbacks(opt: ATShared.OptimizerConf):
	optimizer = pms.CMAOptimizer(popsize=opt.popsize, sigma=opt.sigma, minsigma=opt.minsigma)
	maxIter = pms.MaxIter(opt.maxstep, verbose=True)
	patience = pms.Patience(opt.patience, verbose=True)
	callbacks = [maxIter, patience]
	return optimizer, callbacks
	