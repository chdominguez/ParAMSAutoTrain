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
"""

    selectOptimizationTechnique = input(availableTechniques) or "0"

    try:
        optT = int(selectOptimizationTechnique)
    except:
        print("Error selecting optimization technique. Aborting.\n")
        sleep(2)
        tools()

    if optT > 4 or optT < 1:
        print(f"Technique {optT} does not exist. Aborting.\n")
        sleep(2)
        tools()

    paramsPerRound = input("How many parameters to optimize each round? (minimum 3, currently only applies to random technique): ") or "3"

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
    pInterface.atoms = atoms
    pInterface.avoidAtoms = avoidAtoms
    pInterface.blocks = blocks
    pInterface.categos = categos
    pInterface.optTechnique = selectOptimizationTechnique
    pInterface.paramsPerRound = paramsPerRound

    return pInterface

def editParamConfig(loadedJSON):

    ffield = loadedJSON["files"]["initialff"]

    tmp = tempFile("ffield", ffield)

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

def trainingSetEditor():
    print("ha")

def fileExtractor():
    description="""This tool extracts the training info from an autotran.json file. The output files are:
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
    print("Extracting initial force field set...\n")
    sleep(1)
    initialff = ATShared.tempFile("training_set.yaml", configuration.data.initialff)
    print("Extracting training set...\n")
    sleep(1)
    training_set = ATShared.tempFile("training_set.yaml", configuration.data.training_set)
    print("Extracting validation set...\n")
    sleep(1)
    validation_set = ATShared.tempFile("validation_set.yaml", configuration.data.validation_set)
    print("Extracting job collection...\n")
    sleep(1)
    job_collection = ATShared.tempFile("job_collection.yaml", configuration.data.jobcol)
    print("Extracting job collection engines...\n")
    sleep(1)
    job_collection_engines = ATShared.tempFile("job_collection_engines.yaml", configuration.data.joben)

    print("Files sucessfully extracted\n")
    sleep(1)
    tools()

def tools():
    available_tools = """[1] AutoTrain.json generator
[2] AutoTrain.json editor
[3] Training set editor
[4] File extractor
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

    else:
        import AutoTraining
        AutoTraining.selectSubprogram()