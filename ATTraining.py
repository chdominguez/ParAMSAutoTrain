from audioop import add
import json
from tabnanny import verbose
import scm.params as params
import ATShared
from time import sleep

def train(jsonAsARG: str = "NULL"):

    if jsonAsARG != "NULL":
        ATShared.verifyFiles([jsonAsARG])
        configuration = ATShared.loadJSONIntoTrainConfiguration(jsonAsARG)
    else:
        configurationFile = input("Load training configuration file [autotrain.json]: ") or "autotrain.json"
        ATShared.verifyFiles([configurationFile])
        configuration = ATShared.loadJSONIntoTrainConfiguration(configurationFile)

    tmp = ATShared.tempFile("ffield", configuration.data.initialff)
    setupInterface(tmp.fileName, interConf=configuration.parameterInterface)
    tmp.destroy()

    print(f"Start optimizing {configuration.name}\n")
    
    
    
    
def setupInterface(ffieldFile: str, interConf: ATShared.ParamInterface):
    interface = params.ReaxFFParameters(ffieldFile)

    getAllParams(interface=interface, interConf=interConf)

    return interface

def getAllParams(interface: params.ReaxFFParameters, interConf: ATShared.ParamInterface):
    params = interface[:]
    wantedParams = []
    for param in params:
        addToList = False
        if len([i for i in interConf.atoms if i in param.atoms]) > 0:
            if len([i for i in interConf.avoidAtoms if i in param.atoms]) == 0:
                addToList = True
        if addToList:
            wantedParams.append(param.name)

    print(f"total params: {len(wantedParams)}")

# def randomParams(interface):


# def atomParams():

# def blockParams():

# def categoParams():


def setupOptimizerCallbacks(opt: ATShared.OptimizerConf):
    optimizer = params.CMAOptimizer(popsize=opt.popsize, sigma=opt.sigma, minsigma=opt.minsigma)
    maxIter = params.MaxIter(opt.maxstep, verbose=True)
    patience = params.Patience(opt.patience, verbose=True)
    callbacks = [maxIter, patience]
    return optimizer, callbacks
    