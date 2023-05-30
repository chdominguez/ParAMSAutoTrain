# AutoTrain
AutoTrain is a small python program which connects with the more advanced ParAMS computational package. This program helps during the parametrization of ReaxFF forcefields.

# Features
AutoTrain has some features that make it appealing:
* Compact data storage: AutoTrain saves a unique file which contains all the necessary files for the PLAMS library to work: training_set, job_collection...
* Easy configuration: AutoTrain contains  tools to manage the configuration of optimizations.
* Restart: AutoTrain will save the optimization procedure at each iteration so it can restart it if there is an early stop.

# Requirements
* A valid installation of the [SCM](scm.com) package.
* A Debian based Linux distribution

# Installing
1. [Download](https://github.com/chdominguez/ParAMSAutoTrain/releases/download/1.5/autotrain_1.5-1_all.deb) the latest release
2. Install it with `sudo dpkg -i autotrain_1.5-1_all.deb`
3. Done!

# Usage
 `autotrain` justs starts the program normally. There you can access the training tools.

 `autotrain -h` shows help.
 
 `autotrain -i <input> -o <output>` starts training the force field with the configuration provided in the input json file. The logfile will be written in output.

# License
MIT License

Copyright (c) 2022 Christian Domínguez Dalmases

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
