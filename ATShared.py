from time import sleep
import sys
import json
import os

class tempFile:
    fileName = "autotrain.tmp"

    def destroy(self):
        os.system(f"rm -rf {self.fileName}")

    def __init__(self, name: str, fromString: str):
        self.fileName = name + ".tmp"
        with open(self.fileName, "w") as f:
            f.write(fromString)

class RequiredFiles:
    """Required files"""
    initialff = "initial.ff"
    jobcol = "job_collection.yaml"
    joben = "job_collection_engines.yaml"
    training_set = "training_set.yaml"
    validation_set = "GENERATE_FROM_TRAINING_20"

class OptimizerConf:
    """Optimizer configuration"""
    sigma = float(0.2)
    minsigma = float(1e-4)
    popsize = int(15)
    maxstep = int(1000)
    patience = int(500)
    loss = "rmse"
    iterations = int(5)

class ParamInterface:
    atoms = []
    blocks = []
    categos = []
    avoidAtoms = []
    optTechnique = "1"
    paramsPerRound = "3"

class TrainConfiguration:
    name = "AutoTrain"
    parameterInterface = ParamInterface()
    data = RequiredFiles()
    optConf = OptimizerConf()

def loadJSONIntoTrainConfiguration(file):
    loadedJSON = loadJSON(file)
    configuration = TrainConfiguration()

    configuration.name = loadedJSON["name"]

    jsonINTERFACE = loadedJSON["parameterInterface"]
    interface = ParamInterface()
    interface.optTechnique = jsonINTERFACE["optTechnique"]
    interface.paramsPerRound = jsonINTERFACE["paramsPerRound"]
    interface.atoms = jsonINTERFACE["atoms"]
    interface.avoidAtoms = jsonINTERFACE["avoidAtoms"]
    interface.blocks = jsonINTERFACE["blocks"]
    interface.categos = jsonINTERFACE["categos"]
    configuration.parameterInterface = interface
    
    jsonDATA = loadedJSON["files"]
    data = RequiredFiles()
    data.initialff = jsonDATA["initialff"]
    data.jobcol = jsonDATA["jobcol"]
    data.joben = jsonDATA["joben"]
    data.training_set = jsonDATA["training_set"]
    data.validation_set = jsonDATA["validation_set"]
    configuration.data = data

    jsonOptimizer = loadedJSON["optimizer"]
    optConf = OptimizerConf()
    optConf.sigma = jsonOptimizer["sigma"]
    optConf.minsigma = jsonOptimizer["minsigma"]
    optConf.popsize = jsonOptimizer["popsize"]
    optConf.maxstep = jsonOptimizer["maxstep"]
    optConf.patience = jsonOptimizer["patience"]
    optConf.loss = jsonOptimizer["loss"]
    optConf.iterations = jsonOptimizer["iterations"]
    configuration.optConf = optConf

    return configuration

def checkIfInList(list, items, msg="does not exist. Aborting."):
    for split in items:
        if not split in list:
            print(f"{split} {msg}\n")
            sleep(2)
            return False
    return True
            

def loadFileAsString(file):
    with open(file) as f:
        loadedString = f.read()
    return loadedString

def loadModules():
    try: 
        import scm
    except ImportError or ModuleNotFoundError:
        print(f"Could not find the SCM module. Are you running the script with asmpython?")
        sys.exit(1)
    try: 
        import yaml
    except ImportError or ModuleNotFoundError:
        print(f"Could not find the Python YAML module. Try installing it with pip3 install yaml")
        sys.exit(1)

def verifyFiles(files):
    from os.path import exists

    for file in files:
        if not exists(file):
            print(f"ERROR! File {file} does not exist, aborting")
            sleep(2)
            import AutoTraining
            AutoTraining.main()


def optimizerToJSON(opt: OptimizerConf):
    config = {
            "sigma": opt.sigma,
            "minsigma": opt.minsigma,
            "popsize": opt.popsize,
            "maxstep": opt.maxstep,
            "patience": opt.patience,
            "loss": opt.loss,
            "iterations": opt.iterations 
            }
    return config

def interfaceToJSON(interface: ParamInterface):
    interface = {
        "atoms": interface.atoms,
        "avoidAtoms": interface.avoidAtoms,
        "blocks": interface.blocks,
        "categos": interface.categos,
        "optTechnique": interface.optTechnique,
        "paramsPerRound": interface.paramsPerRound
    }
    return interface

def filesToJSON(files: RequiredFiles):
    reqFiles = {
                "initialff": files.initialff,
                "jobcol": files.jobcol,
                "joben": files.joben,
                "training_set": files.training_set,
                "validation_set": files.validation_set
                }
    return reqFiles

def writeJSON(trainConfig: TrainConfiguration):
    
    # Data to be written
    autotrainJSON = {
        "name": trainConfig.name,
        "optimizer": optimizerToJSON(trainConfig.optConf),
        "parameterInterface": interfaceToJSON(trainConfig.parameterInterface),
        "files": filesToJSON(trainConfig.data)
    }
 
    # Writing to sample.json
    saveJSONToFile(trainConfig.name, autotrainJSON)

def saveJSONToFile(name, object):
    json_object = json.dumps(object, indent=4)
    with open(f"{name}.json", "w") as outfile:
        outfile.write(json_object)
    print(f"{name} sucesfully saved!")
    sleep(2)

def loadJSON(file):
    with open(file) as f:
        loadedJSON = json.load(f)
    return loadedJSON