from decomposition import *
from multiprocessing import Process, Queue
import time

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
        if timeTaken >= 5:
            print("Solve need more then 30 minutes")
            q.put("took too long")
            p.terminate()
            break

    result = q.get()
    timesFile.write("File " + file + " needed " + str(timeTaken) + " seconds to finish with result " + result + "\n")
    # Cleanup
    p.join()
timesFile.close()