from decomposition import *
from originalFormluation import *
from multiprocessing import Process, Queue
import time

timeLimit = 60

def decomp_time():
    fileName = "elapsed times (without cuts).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, 2000):
        testFiles.append('testcases/Example' + str(num) + '.txt')
    
    times = {}
    
    q = Queue()
    
    for file in testFiles:
        dataMap = read_data(file)
        if (dataMap['numEmployees'] >= 20 or dataMap['numShifts'] == 3):
            continue
        
        p = Process(target=decomp, name="decomp", args=(q, file))
        p.start()
    
        startTime = time.time()
        timeTaken = 0
        while p.is_alive():
            timeTaken = time.time() - startTime
            if timeTaken >= timeLimit:
                print("Solve need more then 30 minutes")
                p.terminate()
                break
    
        result = q.get()
        if timeTaken >= timeLimit:
            timesFile.write("File " + file + " didn't complete in time.\n")
        else:
            timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
        # Cleanup
        p.join()
        times[file] = timeTaken
    timesFile.close()
    
def original_time():
    fileName = "elapsed times (original).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, 2000):
        testFiles.append('testcases/Example' + str(num) + '.txt')
    
    times = {}
    
    q = Queue()
    
    for file in testFiles:
        dataMap = read_data(file)
        if (dataMap['numEmployees'] >= 20 or dataMap['numShifts'] == 3):
            continue
        
        p = Process(target=originalRecipe, name="original", args=(q, file))
        p.start()
    
        startTime = time.time()
        timeTaken = 0
        while p.is_alive():
            timeTaken = time.time() - startTime
            if timeTaken >= timeLimit:
                print("Solve need more then 30 minutes")
                p.terminate()
                q.put("Infeasible")
                break
    
        result = q.get()
        if timeTaken >= timeLimit:
            timesFile.write("File " + file + " didn't complete in time.\n")
        else:
            timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
        # Cleanup
        p.join()
        times[file] = timeTaken
    timesFile.close()