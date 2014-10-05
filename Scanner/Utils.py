outputfile = ""

def setupLog(logFile):
	outputfile = logFile

def log(line):
        print line
        if outputfile <> "":
                with open(outputfile, "a") as f:
                        f.write(line + '\n')
