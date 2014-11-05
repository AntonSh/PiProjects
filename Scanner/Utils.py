outputfile = ""

def setupLog(logFile):
	global outputfile
	outputfile = logFile

def log(line):
        print line
        if outputfile <> "":
                with open(outputfile, "a") as f:
                        f.write(line + '\n')
