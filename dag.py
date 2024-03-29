from gurobipy import *
from fileReader import *
import math
import time

testFiles = []
for num in range(1, 2):
    testFiles.append('testcases/Example' + str(num) + '.txt')

times = {}

for file in testFiles:
    dataMap = read_data(file)
    
    
    
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
    W = []
    
    DW = range(maxWork)
    
    # current length of shift block we are currently looking for 
    L = minWork
    
    start = time.time()
    
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
            W.append(b)
    
        else:
            L = L + 1
                    
    print("feasible work blocks found")
  
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
    B = B + O
    #Computes the converage of a shift block b starting on day d
    #return: list of shifts s in day g that are covered
    def Coverage(b,d):
        currentDay = d
        coverageList = []
        
        for i in b:
            tupleList = tuple([i,currentDay])
            coverageList.append(tupleList)
            currentDay = (currentDay + 1) % planningLength
        
        return coverageList
    
    #given the shift s in day d that is needed to be covered
    #return the shift block b staring on day g that is able to cover this
    def C(s,d):
        CList = []
        for g in G:
            for b in range(len(W)):
                if (s,d) in Coverage(W[b],g):
                    CList.append(tuple([b,g]))
        return CList
    
    
    
    
    def additionEmp (n1, n2):
        additionCount = 0
        
        shiftBlock1 = W[n1[0]]
        shiftBlock2 = W[n2[0]]
        
        #first day of the block
        startDay1 = n1[1]
        startDay2 = n2[1]
        
        #length of the shift block
        blockLeng1 = len(shiftBlock1)
        blockLeng2 = len(shiftBlock2)
        
        #last day of the block
        blockEnd1 = startDay1 + blockLeng1 - 1
        blockEnd2 = startDay2 + blockLeng2 - 1
        
        #if the first block goes beyond the end of the schedule, 
        #we need an additional employee to take the exceeding part 
        if blockEnd1 > planningLength - 1:
            additionCount += 1
     
        #if the second schedule is to be started before or during the first block
        #we need an additional employee to take the second block
        if blockEnd1 % planningLength >= startDay2:
            additionCount += 1
    
        #if the second block goes beyond the end of the schedule, 
        #we need an additional employee to take the exceeding part    
        if blockEnd2 > planningLength - 1:
            additionCount += 1
        
        return additionCount
    
    def cantUseNodes(N):
        cantUse = []
        for n1 in N:
            for n2 in N:
                shiftBlock1 = W[n1[0]]
                shiftBlock2 = W[n2[0]]
        
                #first day of the block
                startDay1 = n1[1]
                startDay2 = n2[1]
        
                #length of the shift block
                blockLeng1 = len(shiftBlock1)
                blockLeng2 = len(shiftBlock2)
        
                #last day of the block
                blockEnd1 = (startDay1 + blockLeng1 - 1) % planningLength
                blockEnd2 = (startDay2 + blockLeng2 - 1) % planningLength
                
                index1 = N.index(n1)
                index2 = N.index(n2)
                
                # the number of day offs between the last day of block1 and first day of block2
                offwork = startDay2 - blockEnd1 - 1
                
                # if the second block is worked by another employee, the offwork interval
                # goes over to the next week
                if blockEnd1 >= startDay2:
                    offwork += 7
    
                # check if the offwork lengths satisfy the max and min lengths
                if offwork < minD or offwork > maxD:
                    if (index1,index2) not in cantUse:
                        cantUse.append((index1,index2))
                
                # check forbidden sequence of length 3
                if len(F3) > 0 and offwork == 1:
                    for i in F3:
                        if shiftBlock1[blockLeng1 - 1] == i[0] and shiftBlock2[0] == i[1]:
                            if (index1,index2) not in cantUse:
                                cantUse.append((index1,index2))
                
                
        return cantUse
    
    def getLength (b):
        block = B[b]
        
        return len(block)
    
    BW = range(len(B))
    WL = range(len(W))
    OL = range(len(O))
    
    def maxAllowance(block,start):
        k = Model("maximum allowance of block b starting on d") 
        k.setParam('OutputFlag',0)
        #print(block,start)
        X = {}
        #number of times that shift block b starts from day d
        X = {(b,d):k.addVar(vtype = GRB.INTEGER) for d in G for b in WL}
    
        Demand = {(s,d):k.addConstr( quicksum(X[b,g] for (b,g) in C(s,d)) == workDemand[s][d]) for s in S for d in G}
        
        k.setObjective(X[block, start], GRB.MAXIMIZE)
        k.optimize()
        
        if k.status == GRB.INF_OR_UNBD:
            k.setParam("DualReductions",0)
            k.optimize()
        
        maximumCount = 0
        if k.status == GRB.OPTIMAL:
            maximumCount = X[block,start].x
        return int(round(maximumCount))
    
    def maxDayOffs(block):
        totalWork = 0
        bLength = len(block)
        
        for s in S:
            for d in G:
                totalWork += workDemand[s][d]
        
        totalDayOffs = schedulingLength - totalWork
        
        maxNum = math.floor(totalDayOffs/bLength)
        
        return maxNum
    
      

    
    maximumAllowance = {}
    maximumAllowanceAnyDay = {}
    START = time.time()
    for b in BW:
        if B[b] in W:
            for d in G:
                wIndex = W.index(B[b])
                
                maximumAllowance[b,d] = maxAllowance(wIndex,d)
            maximumAllowanceAnyDay[b] = max(maximumAllowance[b,d] for d in G)
        else:
            maximumAllowanceAnyDay[b] = maxDayOffs(B[b])
    
    print("sets found ")
    FINISHE = time.time()
    print(FINISHE - START)
    M = {}
    
    for b in BW:
        M[b] = range(maximumAllowanceAnyDay[b])
    
    
    Nodes = []
    
    for b in BW:
        for k in M[b]:
            Nodes.append((b,k))
    
    
    
    #B - set of all the blocks; W - set of work blocks; O - set of day off blocks; W+O = B
    print("sets found")
    
    m = Model("DAG")

    X = {(b,k):m.addVar(vtype = GRB.BINARY) for b in BW for k in M[b]}
    
    Y = {(n1,n2):m.addVar(vtype = GRB.BINARY) for n1 in Nodes for n2 in Nodes}
    
    #Conservation of Flows
    OneEdgeIn = {j:m.addConstr(quicksum(Y[i,j] for i in Nodes) <= 1) for j in Nodes}
    OneEdgeOut = {i:m.addConstr(quicksum(Y[i,j] for j in Nodes) <= 1) for i in Nodes}
    
    #Only use k if k-1 is used
    XIncrement = {(b,k):m.addConstr(X[b,k-1] >= X[b,k]) for b in BW for k in M[b]  if k > 0}

    
    #
    WorkGapsLeft = {(n):m.addConstr(quicksum(Y[n,n1] for n1 in Nodes if B[n1[0]] in O) <= 1) for n in Nodes if B[n[0]] in W}
    WorkGapsRight = {(n):m.addConstr(quicksum(Y[n1,n] for n1 in Nodes if B[n1[0]] in O) <= 1) for n in Nodes if B[n[0]] in W}
    
    DayOffGapsLeft = {(n):m.addConstr(quicksum(Y[n,n1] for n1 in Nodes if B[n1[0]] in W) <= 1) for n in Nodes if B[n[0]] in O}
    DayOffGapsRight = {(n):m.addConstr(quicksum(Y[n1,n] for n1 in Nodes if B[n1[0]] in W) <= 1) for n in Nodes if B[n[0]] in O}
    
    NoConsectWork = {(n1,n2):m.addConstr(Y[n1,n2] == 0) for n1 in Nodes for n2 in Nodes if B[n1[0]] in W and B[n2[0]] in W}
    NoConsectDayOffs = {(n1,n2):m.addConstr(Y[n1,n2] == 0) for n1 in Nodes for n2 in Nodes if B[n1[0]] in O and B[n2[0]] in O}
    
    
    
    
    
    #Connect X and Y
    YAndX = {(n1,n2):m.addConstr(X[n1] + X[n2] >= 2 * Y[n1,n2]) for n1 in Nodes for n2 in Nodes}
    
    m.optimize()
    
    
    
    