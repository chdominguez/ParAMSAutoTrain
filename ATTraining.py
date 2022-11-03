from audioop import add
import json
from tabnanny import verbose
import scm.params as pms
import ATShared
from time import sleep
import random

def train(jsonAsARG: str = "NULL"):

    autotrainInfo = """Autotrain. ParAMS configurator and optimizer.
Christian Domínguez
https://github.com/chdominguez/ParAMSAutoTrain
"""
    print(autotrainInfo)

    if jsonAsARG != "NULL":
        ATShared.verifyFiles([jsonAsARG])
        configuration = ATShared.loadJSONIntoTrainConfiguration(jsonAsARG)
    else:
        configurationFile = input("Load training configuration file [autotrain.json]: ") or "autotrain.json"
        ATShared.verifyFiles([configurationFile])
        configuration = ATShared.loadJSONIntoTrainConfiguration(configurationFile)

    print("Loading configuration\n")

    tmp = ATShared.tempFile("ffield", configuration.data.initialff)
    interface = pms.ReaxFFParameters(tmp.fileName)
    tmp.destroy()

    print("Wanted parameters: ")
    wantedParams = getAllWantedParams(interface=interface, interConf=configuration.parameterInterface)

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
    else:
        print("\nNo technique was specified, using random parameters:\n")
        sleep(1)
        blocks = randomParamsBlocks(configuration.parameterInterface.paramsPerRound, wantedParams)
    
    optimize(configuration, blocks, interface)

    print(f"Start optimizing {configuration.name}\n")

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

    bestffield = ""

    if ATShared.verifyFiles(["restart.at"], abort=False):
        restart = ATShared.loadJSON("restart.at")
        checkpoint = True
    else:
        checkpoint = False    

    iterations = int(configuration.optConf.iterations)

    if checkpoint:
        iterations = int(restart["iterations_left"])
        bestffield = restart["bestffield"]
        lastBlock = int(restart["lastblock_index"])

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
            optimizer     = pms.CMAOptimizer(popsize=configuration.optConf.popsize, sigma=configuration.optConf.sigma, minsigma=configuration.optConf.minsigma)
            optimization = pms.Optimization(jc, data_sets, active, optimizer, loss=configuration.optConf.loss, callbacks=callbacks)
            optimization.optimize()
            optimization.summary()
            bestffield = optimization.workdir + "/training_set_results/best/ffield.ff"

            restart = ATShared.Restart
            restart.bestffield = bestffield
            restart.iterations_left = iterations - i - 1
            restart.lastblock_index = p

            ATShared.writeRestartJSON(restart)





def activate(params, interface):
    for p in interface:
        if p in params:
            p.is_active = True
    return interface

def getAllWantedParams(interface: pms.ReaxFFParameters, interConf: ATShared.ParamInterface):
    wantedParams = []
    for param in interface:
        complyAtoms = False
        complyCatego = False
        complyBlock = False

        if len([i for i in interConf.atoms if i in param.atoms]) > 0:
            if len([i for i in interConf.avoidAtoms if i in param.atoms]) == 0:
                complyAtoms = True
        if param.block in interConf.blocks:
            complyBlock = True
            if param.block == "GEN":
                complyAtoms = True
                complyCatego = True
        if param.metadata.category in interConf.categos:
            complyCatego = True
        if complyAtoms and complyBlock and complyCatego:
            print(param.name)
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
        paramBlocks.append(b)
    return paramBlocks 

def blockParams(wantedBlocks, wantedParams):
    paramBlocks = []
    for wblock in wantedBlocks:
        b = []
        for p in wantedParams:
            if p.block == wblock:
                b.append(p)
        paramBlocks.append(b)
    return paramBlocks

def categoParamsBlocks(wantedCategos, wantedParams):
    paramBlocks = []
    for wcatego in wantedCategos:
        b = []
        for p in wantedParams:
            if wcatego == p.metadata.caregory:
                b.append(p)
        paramBlocks.append(b)

def setupOptimizerCallbacks(opt: ATShared.OptimizerConf):
    optimizer = pms.CMAOptimizer(popsize=opt.popsize, sigma=opt.sigma, minsigma=opt.minsigma)
    maxIter = pms.MaxIter(opt.maxstep, verbose=True)
    patience = pms.Patience(opt.patience, verbose=True)
    callbacks = [maxIter, patience]
    return optimizer, callbacks
    