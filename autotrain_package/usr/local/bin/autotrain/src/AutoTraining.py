from ATTraining import train

def selectSubprogram():
    import os
    os.system('clear')

    version = "1.3"
    print(f"Welcome to AutoTraining v{version}\n")
    description = """This software can help you with the training process of a reactive force field (namedly ReaxFF)
This script uses the modules defined in PLAMS, a framework provided by the Amsterdam Modelling Suite (AMS)
    """
    print(description)

    

    selection = input("Select:\n[1] Train a force field\n[2] Tools\n[3] Display help\n[Other] Exit\n") or "0"
    os.system('clear')
    if selection == "1":
        import ATTraining
        ATTraining.train()
    if selection == "2":
        import ATTools
        ATTools.tools()
    if selection == "3":
        displayHelp()

def displayHelp():
    faqs="""
Q: Where can I generate my training files (initial force field, job collection...)?
A: You can use ParAMS to build the required files.

Q: What are configuration (AutoTrain.json) files?
A: You can load the training configuration data (training set, number of iterations, optimizer configuration...) from a JSON file, which lets you run optimizations faster. You can generate a new configuration and save it as a JSON file inside the Tools subprogram.
"""
    print(faqs)
    input("Press any key to go back...")
    selectSubprogram()

def main(argv: str=""):
    import ATShared
    import ATTools
    import ATTraining

    ATShared.loadModules()

    if len(argv) > 1:
        train(argv[-1])
    else:
        selectSubprogram()

    print("\nProgram finished.")


if __name__ == "__main__":
    import sys
    main(argv=sys.argv)


