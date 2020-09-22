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

# S = ['D','A','N']
shiftType = []
for day in ['morning', 'afternoon', 'night']:
    if dataMap[day] != []:
        shiftType.append(dataMap[day][0])
S = range(dataMap['numShifts'])

# T[s][d]
workDemand = dataMap['matrix']

minD = dataMap['minDaysOffLength']
maxD = dataMap['maxDaysOffLength']
minWork = dataMap['minWorkBlockLength']
maxWork = dataMap['maxWorkBlockLength']

# e.g.[1,2,3]
minShift = []

# e.g.[1,2,3]
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
    m = Model('computing feasible shift blocks')
    m.setParam('OutputFlag', 0)
    
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

    

        B.append(b)

    else:
        L = L + 1
                
print("feasible blocks found")

#Computes the converage of a shift block b starting on day d
#return: list of shifts s in day g that are covered
def Coverage(b,d):
    currentDay = d
    coverageList = []
    
    for i in b:
        tupleList = tuple([i,currentDay])
        coverageList.append(tupleList)
        currentDay = (currentDay + 1)%planningLength
    
    return coverageList

#given the shift s in day d that is needed to be covered
#return the shift block b staring on day g that is able to cover this
def C(s,d):
    CList = []
    for g in G:
        for b in range(len(B)):
            if (s,d) in Coverage(B[b],g):
                CList.append(tuple([b,g]))
    return CList


m = Model("master")
m.setParam('OutputFlag',0)

#number of times that shift block b starts from day d
X = {(b,d):m.addVar(vtype = GRB.INTEGER) for d in G for b in range(len(B))}


#sum of blocks b that start from day g that can provide coverage on shift s and day d must equal to the demand s and d. 
OnShiftDemand = {(s,d):m.addConstr( quicksum(X[b,g] for (b,g) in C(s,d)) == workDemand[s][d]) for s in S for d in G}
m.optimize()
print("covers found")

for d in G:
    for b in range(len(B)):
        if X[b,d].x > 0.9:
            print('block ' + str(b) + ' starts ' + str(X[b,d].x) + ' times from day ' + str(d))



