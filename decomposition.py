from gurobipy import *
from fileReader import *

file = "testcases/Example"
num = 1

dataMap = read_data(file+str(num)+".txt")

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
        
        
# e.g. F2[0] = ['N','M']
F2 = dataMap['notAllowedShiftSequences2']

# e.g. ['N','M','A']
F3 = dataMap['notAllowedShiftSequences3']

B = []

DW = range(maxWork)
L = minWork

while L <= maxWork:
    m = Model('RWS')
    
    X = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in DW}
    Y= {(s):m.addVar(vtype = GRB.BINARY) for s in S}
    
    OneShiftPerDay = {(d):m.addConstr(quicksum(X[s,d] for s in S) <= 1) for d in DW}
    minLengthWork = m.addConstr( quicksum(X[s,d] for s in S for d in DW)>= minWork)
    
    if len(F2) > 0:
        ForbiddenSequence2 = {(f): m.addConstr(X[shiftType.index(F2[f][0]),d] + X[shiftType.index(F2[f][1]),d+1] <= 1) for d in DW if d < maxWork-1 
        for f in range(len(F2))}
        
    Length = m.addConstr(quicksum(X[s,d] for s in S for d in DW) == L)
    
    Continuous = {d:m.addConstr(quicksum(X[s,d] for s in S) >= (L - d)/maxWork ) for d in DW}
    Continuous2 = {d:m.addConstr(quicksum(X[s,d] for s in S) <= 1 + (L -d)/maxWork) for d in DW}
    
    shiftUsed = {s:m.addConstr(quicksum(X[s,d] for d in DW)/maxShift[s] <= Y[s]) for s in S}
    
    minLengthShift = {s:m.addConstr(quicksum(X[s,d] for d in DW) >= minShift[s] * Y[s]) for s in S}
    
    maxLengthShift = {s:m.addConstr(quicksum(X[s,d] for d in DW) <= maxShift[s]) for s in S}
    
    #Finding multiple solutions
    if len(B) > 0:
        newSolution = {b:m.addConstr(quicksum(X[s,d] for s in S for d in range(len(b)) if s != b[d]) + quicksum(1 - X[b[d],d] for d in range(len(b))) >= 1) for b in B if len(b) == L}
    
    m.optimize()
    
    if m.status != GRB.INFEASIBLE:
        b = []
        for d in DW:
            for s in S:
                if X[s,d].x > 0.9:
                    b.append(s)
        
        b = tuple(b)
    
        print(b)
    

        B.append(b)

    else:
        L = L + 1
                
print("Solutions found")





