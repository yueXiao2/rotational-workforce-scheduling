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

W = []

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
    if len(W) > 0:
        
        # no-good cut/ rubbish cut: cuts off the discovered solutions in the set B
        newSolution = {b:m.addConstr(quicksum(X[s,d] for s in S for d in range(len(b)) if s != b[d]) + quicksum(1 - X[b[d],d] for d in range(len(b))) >= 1) for b in W if len(b) == L}
    
    m.optimize()
    
    if m.status != GRB.INFEASIBLE:
        b = []
        for d in DW:
            for s in S:
                if X[s,d].x > 0.9:
                    b.append(s)
        
        b = tuple(b)
        W.append(b)

    else:
        L = L + 1


#generate work off blocks
def BreakBlockGen():
    O = []
    for i in range(minD,maxD+1):
        o = []
        for j in range(i):
            o.append(3)
        O.append(tuple(o))
    return O

O = BreakBlockGen()

B = []
for w in W:
    for o in O:
        b = w + o
        if b not in B:
            B.append(b)
        

print("feasible blocks found")
print(len(W))
print(len(B))

#Computes the converage of a shift block b starting on day d
#return: list of shifts s in day g that are covered
def Coverage(b,d):
    currentDay = d
    coverageList = []
    
    for i in b:
        
        if i == 3:
            break
        
        tupleList = tuple([i,currentDay])
        coverageList.append(tupleList)
        currentDay = (currentDay + 1)%planningLength
    
    return coverageList

#given the shift s in day d that is needed to be covered
#return the shift block b staring on day g that is able to cover this
def C(s,d):
    CList = []
    for g in G:
        for b in B:
            if (s,d) in Coverage(b,g):
                CList.append(tuple([b,g]))
    return CList


def maxNumBlocks():
    minLengthBlock = minD + minWork
    
    maxNum = (schedulingLength) / minLengthBlock
    
    return int(maxNum)

def minNumBlocks():
    maxLengthBlock = maxD + maxWork
    
    minNum = (schedulingLength) / maxLengthBlock
    
    return int(minNum)

minBlocks = minNumBlocks()
maxBlocks = maxNumBlocks()

def cantUseNodes(N,k):
    cantUse = []
    for n1 in N:
        for n2 in N:
            
            if k == 0 and n1 != ('start'):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
                continue
            
            if k == maxBlocks+1 and n2 != ('sink'):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
                continue
            
            
            if n1 == ('start'):
                if n2 == ('sink'):
                    if (n1,n2) not in cantUse:
                        cantUse.append((n1,n2))
                
                if k > 0:
                    if (n1,n2) not in cantUse:
                        cantUse.append((n1,n2))
                continue
            
            if n1 == ('sink'):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
                continue
            
            if n2 == ('sink'):
                if k == 0:
                    if (n1,n2) not in cantUse:
                        cantUse.append((n1,n2))
                continue
            
            if n2 == ('start'):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
                continue
            
            
            shiftBlock1 = n1[0]
            shiftBlock2 = n2[0]
            
            dayOffIndex1 = shiftBlock1.index(3)

            
            #first day of the block
            startDay1 = n1[1]
            startDay2 = n2[1]
    
            #length of the shift block
            blockLeng1 = len(n1)
            
            numDayOffs1 = blockLeng1 - dayOffIndex1
    
            #last day of the block
            blockEnd1 = startDay1 + blockLeng1 - 1 % planningLength
            
            if  startDay2 != (blockEnd1 + 1 % planningLength):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
            
            # check forbidden sequence of length 3
            if len(F3) > 0 and numDayOffs1 == 1:
                for i in F3:
                    if shiftBlock1[dayOffIndex1 - 1] == i[0] and shiftBlock2[0] == i[1]:
                        if (n1,n2) not in cantUse:
                            cantUse.append((n1,n2))
    return cantUse
        


Nodes = []



Num = range(maxBlocks+2)



for b in B:
    for d in G:
        Nodes.append((b,d))

Nodes.append(("start"))
Nodes.append(("sink"))
print("before K")

K = {}
K[0] = cantUseNodes(Nodes,0)
regular = cantUseNodes(Nodes,1)
for n in Num:
    if n > 0:
        K[n] = regular

m = Model("Alt Model")
print("after K")
#Variables

#Node (b1,d1) is followed by node (b2,d2) at the kth block
Y = {(n1,n2,n) : m.addVar(vtype=GRB.BINARY) for n1 in Nodes for n2 in Nodes for n in Num 
     if (n1,n2) not in K[n]}

print("variables set up")
#Constraints

OnlyOneStart = m.addConstr(quicksum(Y[n1,n2,k] for (n1,n2,k) in Y if k == 0) == 1)

OnlyOneEnd = m.addConstr(quicksum(Y[n1,n2,k] for (n1,n2,k) in Y if n2 == ('sink')) == 1)


#Conservation of flow
Conservation = {(n1,k):m.addConstr(quicksum(Y[n2,n1,k] for (n2,nn,kk) in Y if nn == n1 and kk == k) - quicksum(Y[n1,n2,k+1] for (nn,n2,kk) in Y if nn == n1 and kk == k + 1) == 0) 
for (n1,n,k) in Y if k > 0 and k < maxBlocks+1}
#
FlowIn = {(n1,k):m.addConstr(quicksum(Y[n2,n1,k] for (n2,nn,kk) in Y if nn == n1 and k == kk) <= 1) for (n,n1,k) in Y}

FlowOut = {(n1,k):m.addConstr(quicksum(Y[n1,n2,k] for (nn,n2,kk) in Y if nn == n1 and k == kk) <= 1) for (n1,n,k) in Y}

ExactScheduleLength = m.addConstr(quicksum(Y[n1,n2,k] * len(n1) for (n1,n2,k) in Y if n1 != ("start")) == schedulingLength)

DemandCoverage = {(s,d):m.addConstr(quicksum(Y[n1,n2,k] for (n1,n2,k) in Y if n1 != ("start") and (n1[0],n1[1]) in C(s,d)) == workDemand[s][d]) for s in S for d in G}

def callback(model, where):
    if where == GRB.Callback.MIPSOL:
        YV = {k: v for (k,v) in zip(Y.keys(), model.cbGetSolution(list(Y.values()))) if v > 0.9}

        for n in YV:
            if n[0] == ("start"):
                firstNode = n[1]
                FV = n
            
            if n[1] == ("sink"):
                lastNode = n[0]
            
        
    
        for n in YV:
            if n[0] == lastNode:
               LV = n
               
        FNodes = cantUseNodes(Nodes,1)
       
        if (lastNode,firstNode) in FNodes:
           
           for k in Num:
               if k > 0:
                   model.cbLazy((1 - Y[("start"),firstNode,0]) + (1 - Y[lastNode,("end"),k]) - 1 >= 0)

m.setParam('LazyConstraints',1)
m.optimize(callback)
print(minD)
if m.status != GRB.INFEASIBLE:
    for b in B:
        for d in G:
            for k in M[b,d]:
                if X[b,d,k].x > 0.9:
                    print(b,d)
    for n1 in Nodes:
        for n2 in Nodes:
            if Y[n1, n2].x > 0.9:
                (b1,d1,k1) = n1
                (b2,d2,k2) = n2
                print("Shift block", b1, "starts on day", d1, k1,'times --------->',"and shift block", b2, "starts on day", d2,k2,'times')
                print("-------------------------------------------")