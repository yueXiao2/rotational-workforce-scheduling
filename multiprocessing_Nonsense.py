from decomposition import *
from originalFormluation import *
from decomposition_initial_cuts import *
from multiprocessing import Process, Queue
from matplotlib import pyplot as plt
from decomposition_master_extension import *
import time

timeLimit = 10*60
dataSetUsed = 2000

times1 = {}
times2 = {}
times3 = {}
times4 = {}

def constraints(dataMap):
    return (dataMap['numEmployees'] > 20)

def decomp_cuts_time():
    fileName = "elapsed times (with cuts).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, dataSetUsed):
        testFiles.append('testcases/Example' + str(num) + '.txt')
        
    q = Queue()
    
    count = 0
    
    for file in testFiles:
        dataMap = read_data(file)
        if constraints(dataMap):
            continue
        
        count += 1
        
        if count == 12:
            break
        
        p = Process(target=decompCuts, name="decompCuts", args=(q, file))
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
    
        print("Done")
        result = q.get()
        if timeTaken >= timeLimit:
            timesFile.write("File " + file + " didn't complete in time.\n")
        else:
            timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
        # Cleanup
        p.join()
        times1[file] = timeTaken
    timesFile.close()

def decomp_time():
    fileName = "elapsed times (without cuts).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, dataSetUsed):
        testFiles.append('testcases/Example' + str(num) + '.txt')
        
    q = Queue()
    
    count = 0
    
    for file in testFiles:
        dataMap = read_data(file)
        if constraints(dataMap):
            continue
        
        count += 1
        
        if count == 12:
            break
        
        p = Process(target=decomp, name="decomp", args=(q, file))
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
    
        print("Done")
        result = q.get()
        if timeTaken >= timeLimit:
            timesFile.write("File " + file + " didn't complete in time.\n")
        else:
            timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
        # Cleanup
        p.join()
        times2[file] = timeTaken
    timesFile.close()
    
def original_time():
    fileName = "elapsed times (original).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, dataSetUsed):
        testFiles.append('testcases/Example' + str(num) + '.txt')
    
    q = Queue()
    
    count = 0
    
    for file in testFiles:
        dataMap = read_data(file)
        if constraints(dataMap):
            continue
        
        count += 1
        
        if count == 12:
            break
        
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
        times3[file] = timeTaken
    timesFile.close()
    
def master_time():
    fileName = "elapsed times (original).txt"
    
    timesFile = open(fileName,'w')
    
    testFiles = []
    for num in range(1, dataSetUsed):
        testFiles.append('testcases/Example' + str(num) + '.txt')
    
    q = Queue()
    
    count = 0
    
    for file in testFiles:
        dataMap = read_data(file)
        if constraints(dataMap):
            continue
        
        count += 1
        
        if count == 12:
            break
        
        p = Process(target=decomp_master, name="Decomp Master", args=(q, file))
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
    
        print("Done")
        result = q.get()
        if timeTaken >= timeLimit:
            timesFile.write("File " + file + " didn't complete in time.\n")
        else:
            timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
        # Cleanup
        p.join()
        times4[file] = timeTaken
    timesFile.close()
    
def run_all():
    decomp_cuts_time()
    original_time()
    master_time()
    decomp_time()
