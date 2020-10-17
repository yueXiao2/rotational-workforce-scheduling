from gurobipy import *
from fileReader import *
import time
from numpy import mean

fileName = "elapsed times (original).txt"

systemTime = time.time()

timesFile = open(fileName,'w')

testFiles = []
for num in range(16, 17):
    testFiles.append('testcases/Example' + str(num) + '.txt')

times = {}

for file in testFiles:
    
    dataMap = read_data(file)
    
# =============================================================================
#     ################################################################
#    if (dataMap['numEmployees'] >= 20 or dataMap['numShifts'] == 3):
#        continue
#     
#     ###############################################################
# =============================================================================
    print(file)
    
    planningLength = dataMap['scheduleLength']
    G = range(planningLength)
    
    numEmployee = dataMap['numEmployees']
    E = range(numEmployee)
    
    schedulingLength = planningLength * numEmployee
    D = range(schedulingLength)
    
    shiftType = []
    for day in ['morning', 'afternoon', 'night']:
        if dataMap[day] != []:
            shiftType.append(dataMap[day][0])
    S = range(dataMap['numShifts'])
    
    workDemand = dataMap['matrix']
    
    minD = dataMap['minDaysOffLength']
    maxD = dataMap['maxDaysOffLength']
    minWork = dataMap['minWorkBlockLength']
    maxWork = dataMap['maxWorkBlockLength']
    minShift = []
    maxShift = []
    for day in ['morning', 'afternoon', 'night']:
        if dataMap[day] != []:
            minShift.append(dataMap[day][1])
            maxShift.append(dataMap[day][2])
    
    F2 = dataMap['notAllowedShiftSequences2']
    
    F3 = dataMap['notAllowedShiftSequences3']
    
    start = time.time()
    m = Model('RWS')
    
    #Varibles
    X = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in D}
    Y = {d:m.addVar(vtype = GRB.BINARY) for d in D}
    Z = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in D}
    

    shiftConverage = {(s,d):m.addConstr(
            quicksum( X[s,dd] for dd in D if (dd % planningLength) == d) == workDemand[s][d]) 
            for s in S for d in G}
    
    maxDayOffs = {d:m.addConstr(quicksum(X[s,dd] for s in S for dd in range(d,min((d+maxD+1),len(D)))) >= 1) 
                                    for d in D}
    
    if (minD > 1):
        minDayOffs = {d:m.addConstr(1 - quicksum(X[s,d] for s in S) <= 2 - quicksum((X[s,d-1] + X[s,d+1]) for s in S)) 
                                                    for d in D if (d > 0 and d < schedulingLength-1)}

    
    maxWorkDays = {d:m.addConstr(quicksum(X[s,dd] for s in S for dd in range(d,min(d+maxWork+1,len(D)))) <= maxWork) 
                                                for d in D}
    
    minWorkDays = {d:m.addConstr(Y[d]<= (quicksum(X[s,dd] for s in S for dd in range(d,min(d+minWork,len(D))))/minWork)) 
                                    for d in D}
    
    shiftSequence = {(s,d):m.addConstr(X[s,d+minWork-1] <= quicksum( Y[dd] for dd in range(d,d+minWork))) 
                        for s in S for d in D if d < schedulingLength - minWork}
    
    if len(F2) > 0:
        forbidden2 = {(f,d):m.addConstr(X[shiftType.index(F2[f][0]),d] <= 1 - X[shiftType.index(F2[f][1]),d+1]) for f in range(len(F2)) 
                        for d in D if d < schedulingLength-1}
    
    if len(F3) > 0:
        forbidden3 = {(f,d):m.addConstr(
                X[shiftType.index(F3[f][0]),d] 
                <= 1 + quicksum(X[s,d+1]  
                for s in S) - X[shiftType.index(F3[f][1]),d+2])
                for f in range(len(F3)) for d in D if d < schedulingLength - 2}
    
    
    OneShiftPerDay = {d:m.addConstr(quicksum(X[s,d] for s in S) <=1) for d in D}
    
    MaxLengthShift = {(s,d):m.addConstr(quicksum( X[s,dd] for dd in range(d,min(d+maxShift[s]+1,len(D))))<=maxShift[s]) 
                            for s in S for d in D}
    
    MinLengthShift1 = {(s,d):m.addConstr(Z[s,d] <= (quicksum(X[s,dd] for dd in range(d,min(d+minShift[s],len(D)-1)))/minShift[s])) 
                for s in S for d in D}
    
    minLengthShift2 = {(s,d):m.addConstr( X[s,d+minShift[s]-1] <= quicksum(Z[s,dd] for dd in range(d,d+minShift[s])))
                        for s in S for d in D if d < schedulingLength - minShift[s]}
    
    
    m.optimize()
    
    end = time.time()
    timeElapsed = end - start
    times[file] = timeElapsed
    
    fileStr = file +" "+str(timeElapsed) + "\n"
    print(fileStr)
    
    timesFile.write(fileStr)
    timesFile.close()
    
    print("time taken",timeElapsed)
    
# =============================================================================
#     for d in D:
#          for s in S:
#              if X[s,d].x > 0.9:
#                  print(shiftType[s],"on day",d,":",X[s,d].x)
# =============================================================================
