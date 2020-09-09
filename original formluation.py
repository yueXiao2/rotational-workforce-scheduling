from gurobipy import *
from fileReader import *

testFiles = []
for num in range(1, 2001):
    testFiles.append('testcases/Example' + str(num) + '.txt')

for file in testFiles:
    dataMap = read_data('testcases/Example1.txt')
    
    planningLength = dataMap['scheduleLength']
    G = range(planningLength)
    
    numEmployee = dataMap['numEmployees']
    E = range(numEmployee)
    
    schedulingLength = planningLength * numEmployee
    D = range(schedulingLength)
    
    shiftType = ["D","A","N"]
    S = range(len(shiftType))
    print(planningLength, numEmployee)
    
    workDemand = dataMap['matrix']
    
    minD = dataMap['minDaysOffLength']
    maxD = dataMap['maxDaysOffLength']
    minWork = dataMap['minWorkBlockLength']
    maxWork = dataMap['maxWorkBlockLength']
    minShift = [dataMap['morning'][1],dataMap['afternoon'][1], dataMap['night'][1]]
    maxShift = [dataMap['morning'][2],dataMap['afternoon'][2], dataMap['night'][2]]
    
    F2 = dataMap['notAllowedShiftSequences2']
    
    #F3 = dataMap['notAllowedShiftSequences3']
    
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
    
    minDayOffs = {d:m.addConstr(1 - quicksum(X[s,d] for s in S) <= 2 - quicksum((X[s,d-1] + X[s,d+1]) for s in S)) 
                                                for d in D if (d > 0 and d < schedulingLength-1)}
    
    maxWorkDays = {d:m.addConstr(quicksum(X[s,dd] for s in S for dd in range(d,min(d+maxWork+1,len(D)))) <= maxWork) 
                                                for d in D}
    
    minWorkDays = {d:m.addConstr(Y[d]<= (quicksum(X[s,dd] for s in S for dd in range(d,min(d+minWork,len(D))))/minWork)) 
                                    for d in D}
    
    shiftSequence = {(s,d):m.addConstr(X[s,d+minWork-1] <= quicksum( Y[dd] for dd in range(d,d+minWork))) 
                        for s in S for d in D if d < schedulingLength - minWork}
    
    forbidden2 = {(f,d):m.addConstr(X[shiftType.index(F2[f][0]),d] <= 1 - X[shiftType.index(F2[f][1]),d+1]) for f in range(len(F2)) 
                        for d in D if d < schedulingLength-1}
    
    #forbidden 3
    
    
    OneShiftPerDay = {d:m.addConstr(quicksum(X[s,d] for s in S) <=1) for d in D}
    
    print(maxShift)
    
    MaxLengthShift = {(s,d):m.addConstr(quicksum( X[s,dd] for dd in range(d,min(d+maxShift[s]+1,len(D))))<=maxShift[s]) 
                            for s in S for d in D}
    
    MinLengthShift1 = {(s,d):m.addConstr(Z[s,d] <= (quicksum(X[s,dd] for dd in range(d,min(d+minShift[s],len(D)-1)))/minShift[s])) 
                for s in S for d in D}
    
    minLengthShift2 = {(s,d):m.addConstr( X[s,d+minShift[s]-1] <= quicksum(Z[s,dd] for dd in range(d,d+minShift[s])))
                        for s in S for d in D if d < schedulingLength - minShift[s]}
    
    
    m.optimize()
    
    for d in D:
         for s in S:
             if X[s,d].x > 0.9:
                 print(shiftType[s],"on day",d+1,":",X[s,d].x)