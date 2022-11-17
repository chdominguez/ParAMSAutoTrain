import numpy as np

def fracpos2xyz(file, debug=0):
	
	if debug == 1:
		print(file)
	
	#Read in POSCAR or CONTCAR file
	f = open(file, "r")
	content = f.readlines()

	#Get all atoms
	Atoms = content[5].split()
	#Get scaling factor, should be 1 for cartesian coordinates
	ScaleFactor = float(content[1])
	#Get vectors, which we won't use, but is helpful
	Vectors = []
	for i in range(2,5):
		Vectors.append(content[i].split())
	#Find how many atoms there are for each type
	AtomTot = content[6].split()

	#Get total number of atoms
	sumAtoms = 0
	for i in AtomTot:
		try:
			sumAtoms += int(i)
		except ValueError:
			raise Exception("Error converting file")

	#Get the coordinates of each atom
	AtomCoords = []
	for i in range(9,sumAtoms+9):
		AtomCoords.append([float(content[i].split()[0]),float(content[i].split()[1]),float(content[i].split()[2])])

	#Vector multiplied by scaling factor. Again not necessary, but was used in prior scripts.
	VectorsAdj = []
	for i in Vectors:
		VectorsAdj.append([float(i[0])*ScaleFactor,float(i[1])*ScaleFactor,float(i[2])*ScaleFactor])

	#Write output file
	f = open(file+".xyz","w")
	#Write number of atoms and a title. Needed for XYZ file
	print(sumAtoms,file=f)
	print("POSCAR to XYZ",file=f)

	#Print the cartesian coordinates, by first multiplying the fractional coordinates with the cell vectors
	for i in range(len(AtomTot)):
		if i==0:
			for j in range(int(AtomTot[i])):
				MatrixMult = np.matmul(AtomCoords[j],VectorsAdj)
				print(Atoms[i],MatrixMult[0],MatrixMult[1],MatrixMult[2],file=f)
		else:
			sumVals = 0
			for j in range(i):
				sumVals+=int(AtomTot[j])
			for j in range(sumVals,int(AtomTot[i])+sumVals):
				MatrixMult = np.matmul(AtomCoords[j],VectorsAdj)
				print(Atoms[i],MatrixMult[0],MatrixMult[1],MatrixMult[2],file=f)
	f.close()

def pos2xyz(file):
	#Read in POSCAR or CONTCAR file
	f = open(file,"r")
	content = f.readlines()

	#Get all atoms
	Atoms = content[0].split()
	AtomTot = content[5].split()

	#Get total number of atoms
	sumAtoms = 0
	for i in AtomTot:
		try:
			sumAtoms += int(i)
		except ValueError:
			raise Exception("Error converting file")

	#Get the coordinates of each atom
	AtomCoords = []
	for i in range(8,sumAtoms+8):
		AtomCoords.append([float(content[i].split()[0]),float(content[i].split()[1]),float(content[i].split()[2])])

	#Write output file
	f = open(file+".xyz","w")
	#Write number of atoms and a title. Needed for XYZ file
	print(sumAtoms,file=f)
	print("POSCAR to XYZ",file=f)

	#Print the coordinates
	for i in range(len(AtomTot)):
		if i==0:
			for j in range(int(AtomTot[i])):
				MatrixMult = AtomCoords[j]
				print(Atoms[i],MatrixMult[0],MatrixMult[1],MatrixMult[2],file=f)
		else:
			sumVals = 0
			for j in range(i):
				sumVals+=int(AtomTot[j])
			for j in range(sumVals,int(AtomTot[i])+sumVals):
				MatrixMult = AtomCoords[j]
				print(Atoms[i],MatrixMult[0],MatrixMult[1],MatrixMult[2],file=f)
	f.close()
