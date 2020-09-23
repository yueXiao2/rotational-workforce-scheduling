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

# current length of shift block we are currently looking for 
L = minWork


# emuerating each element b in B (the set of feasible blocks)
while L <= maxWork:
    m = Model('computing feasible shift blocks')
    m.setParam('OutputFlag', 0)
    
    # 1 if the shift block contains shift s in day d
    X = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in DW}
    
    # if the shift s is used in this feasible block
    Y= {(s):m.addVar(vtype = GRB.BINARY) for s in S}
    
    # your block can only have shift per day
    OneShiftPerDay = {(d):m.addConstr(quicksum(X[s,d] for s in S) <= 1) for d in DW}
    
    # The numebr of shifts in the block must be more than the minimum length
    minLengthWork = m.addConstr( quicksum(X[s,d] for s in S for d in DW)>= minWork)
    
    # enforce forbidden sequence constraint 
    if len(F2) > 0:
        ForbiddenSequence2 = {(f): m.addConstr(X[shiftType.index(F2[f][0]),d] + X[shiftType.index(F2[f][1]),d+1] <= 1) for d in DW if d < maxWork-1 
        for f in range(len(F2))}
        
    # the length of the block must of length L    
    Length = m.addConstr(quicksum(X[s,d] for s in S for d in DW) == L)
    
    # shift blocks must be continous witout day off in between
    #upperbound on shfit block (e.g. the days that below the length L must have one shift)
    Continuous = {d:m.addConstr(quicksum(X[s,d] for s in S) >= (L - d)/maxWork ) for d in DW}
    
    # upperbound on shfit block (e.g. the days that exceed the length L must have no shift)
    Continuous2 = {d:m.addConstr(quicksum(X[s,d] for s in S) <= 1 + (L -d)/maxWork) for d in DW}
    
    # set Y to be 1 for s if s is used in any particular day d
    shiftUsed = {s:m.addConstr(quicksum(X[s,d] for d in DW)/maxShift[s] <= Y[s]) for s in S}
    
    # enforce minimum length of shift s if it is used
    minLengthShift = {s:m.addConstr(quicksum(X[s,d] for d in DW) >= minShift[s] * Y[s]) for s in S}
    
    maxLengthShift = {s:m.addConstr(quicksum(X[s,d] for d in DW) <= maxShift[s]) for s in S}
    
    #Finding multiple solutions
    if len(B) > 0:
        
        # no-good cut/ rubbish cut: cuts off the discovered solutions in the set B
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

#Set of nodes
N = []

for d in G:
    for b in range(len(B)):
        if X[b,d].x > 0.9:
            N.append((b,d))
            print('block ' + str(b) + ' starts ' + str(X[b,d].x) + ' times from day ' + str(d))

def additionEmp (n1, n2):
    additionCount = 0
    
    shiftBlock1 = B[n1[0]]
    shiftBlock2 = B[n2[0]]
    
    #first day of the block
    startDay1 = n1[1]
    startDay2 = n2[1]
    
    #length of the shift block
    blockLeng1 = len(shiftBlock1)
    blockLeng2 = len(shiftBlock2)
    
    #last day of the block
    blockEnd1 = startDay1 + blockLeng1 - 1
    blockEnd2 = startDay2 + blockLeng2 - 1
    
    
    if blockEnd1 > 6:
        additionCount += 1
    
    if blockEnd1 >= startDay2:
        additionCount += 1
    
    if blockEnd2 > 6:
        additionCount += 1
    
    
    return additionCount
        
    


