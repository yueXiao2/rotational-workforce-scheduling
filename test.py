from gurobipy import *
from fileReader import *
import time

#Computes the converage of a shift block b starting on day d
#return: list of shifts s in day g that are covered
def Coverage(b,d, planningLength):
    currentDay = d
    coverageList = []
    
    for i in b:
        if i == 3:
            break
        
        tupleList = tuple([i,currentDay])
        coverageList.append(tupleList)
        currentDay = (currentDay + 1) % planningLength
    
    return coverageList

#given the shift s in day d that is needed to be covered
#return the shift block b staring on day g that is able to cover this
def Something(s,d, G, B, planningLength):
    CList = []
    for g in G:
        for b in range(len(B)):
            if (s,d) in Coverage(B[b],g, planningLength):
                CList.append(tuple([b,g]))
    return CList


def additionEmp (n1, n2, B, planningLength):
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

def cantUseNodes(N, B, planningLength, minD, maxD, F3):
    cantUse = []
    n1Index = 0
    for n1 in N:
        n2Index = 0
        for n2 in N:
            
            if(n1Index == n2Index):
                if (n1Index,n2Index) not in cantUse:
                    cantUse.append((n1Index,n2Index))
                n2Index+=1
                continue
            
            shiftBlock1 = B[n1[0]]
            shiftBlock2 = B[n2[0]]
    
            dayOffIndex1 = shiftBlock1.index(3)

            
            #first day of the block
            startDay1 = n1[1]
            startDay2 = n2[1]
    
            #length of the shift block
            blockLeng1 = len(shiftBlock1)
            
            numDayOffs1 = blockLeng1 - dayOffIndex1
    
            #last day of the block
            blockEnd1 = (startDay1 + blockLeng1 - 1) % planningLength
            
            if  startDay2 != (blockEnd1 + 1 % planningLength):
                if (n1Index,n2Index) not in cantUse:
                    cantUse.append((n1Index,n2Index))
            
            # check forbidden sequence of length 3
            if len(F3) > 0 and numDayOffs1 == 1:
                for i in F3:
                    if shiftBlock1[dayOffIndex1 - 1] == i[0] and shiftBlock2[0] == i[1]:
                        if (n1Index,n2Index) not in cantUse:
                            cantUse.append((n1Index,n2Index))
            n2Index += 1
        n1Index += 1
    return cantUse

def getLength(b, B):
    block = B[b]
    
    return len(block)

def maxAllowance(block, start, G, BW, workDemand, S, B, planningLength):
    k = Model("maximum allowance of block b starting on d") 
    k.setParam('OutputFlag',0)
    #print(block,start)
    X = {}
    #number of times that shift block b starts from day d
    X = {(b,d):k.addVar(vtype = GRB.INTEGER) for d in G for b in BW}

    Demand = {(s,d):k.addConstr( quicksum(X[b,g] for (b,g) in Something(s,d, G, B, planningLength)) == workDemand[s][d]) for s in S for d in G}
    
    k.setObjective(X[block, start], GRB.MAXIMIZE)
    k.optimize()
    
    if k.status == GRB.INF_OR_UNBD:
        k.setParam("DualReductions",0)
        k.optimize()
    
    maximumCount = 0
    if k.status == GRB.OPTIMAL:
        maximumCount = X[block,start].x
    return int(round(maximumCount))

#generate work off blocks
def BreakBlockGen(minD, maxD):
    O = []
    for i in range(minD,maxD+1):
        o = []
        for j in range(i):
            o.append(3)
        O.append(tuple(o))
    return O



def decompCuts(queue, file):
    dataMap = read_data(file)
    print(file)
    
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
                    
    O = BreakBlockGen(minD,maxD)
    B = []
    for w in W:
        for o in O:
            b = w + o
            if b not in B:
                B.append(b)
                
    BW = range(len(B))
    print("feasible blocks found")
    
    
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
    
    Num = range(maxBlocks+1)
    
    
    m = Model("master")
    m.setParam('OutputFlag',0)
    m.setParam('Threads',1)
    
    #number of times that shift block b starts from day d
    X = {(b,d):m.addVar(vtype = GRB.INTEGER) for d in G for b in BW}
    
    Y= {(b,d,n):m.addVar(vtype = GRB.BINARY) for b in BW for d in G for n in Num}
    
    
    #Terrible LP relaxation. Idea: construct a new variable similar to prac 2012 exam
    
    #sum of blocks b that start from day g that can provide coverage on shift s and day d must equal to the demand s and d. 
    OnShiftDemand = {(s,d):m.addConstr( quicksum(X[b,g] for (b,g) in Something(s,d, G, B, planningLength)) == workDemand[s][d]) for s in S for d in G}
    
    #warm up initial cut: given the number of shift blocks == number of off blocks, for a feasible solution to occur, it is necessarily that 
    # the totak day offs >= the number of day off blocks * minimal length of day off block
    #total day offs  = schedule length - total shift days
    #WarmUpLowerCut = m.addConstr(schedulingLength - quicksum( X[b,d] * getLength(b, B) for d in G for b in BW) >= quicksum(X[b,d] for d in G for b in BW) * minD)
    
    
    #warm up initial cut: given the number of shift blocks == number of off blocks, for a feasible solution to occur, it is necessarily that 
    # the totak day offs <= the number of day off blocks * maximum length of day off block
    #total day offs  = schedule length - total shift days
    #WarmUpUpperCut = m.addConstr(schedulingLength - quicksum( X[b,d] * getLength(b, B) for d in G for b in BW) <= quicksum(X[b,d] for d in G for b in BW) * maxD)
    
    #The maximum times that a block b can start on day d
    MaximumAllowanceForBlock = {(b,d):m.addConstr(X[b,d] == quicksum(Y[b,d,n] * n for n in Num)) for b in BW for d in G }
    
    OneYAtATime = {(b,d):m.addConstr(quicksum(Y[b,d,n] for n in Num) == 1) for b in BW for d in G}
    
    ExactLength = m.addConstr(quicksum(X[b,d] * getLength(b,B) for b in BW for d in G ) == schedulingLength)
    
    
    
    SolutionSet = []
    isFeasible = [True]
    
    def Callback (model, where):
        if where == GRB.Callback.MIPSOL:
            print("begining the callback!")
    
            N = []
            XV = {k: v for (k,v) in zip(X.keys(), model.cbGetSolution(list(X.values())))}
            for d in G:
                for b in BW:
                    if XV[b,d] > 0.9:
                        num = round(XV[b,d])
                        for number in range(num):
                            N.append((b,d))
                        #print("block " + str(b) + " starts on day " + str(d) + " " +str(XV[b,d]) + " times")
            
            
            Ysol = []
            YV = {k: v for (k,v) in zip(Y.keys(), model.cbGetSolution(list(Y.values())))}
            for d in G:
                for b in BW:
                    for n in Num:
                        if YV[b,d,n] > 0.9:
                            Ysol.append((b,d,n))
            #Idea of improvement : better way to determine the factors of a hamiltonian circle
            if set(N) not in SolutionSet:
                SolutionSet.append(set(N))
                print("solution appended. current length: " + str(len(SolutionSet)))
            else:
                print("ohhhhh cyclic!")
                isFeasible[0] = False
                model.terminate()
                if queue != None:
                    queue.put("Infeasible")
                return
            
            
            NN = range(len(N))
            K = cantUseNodes(N, B, planningLength, minD, maxD, F3)
            s = Model("subproblem")
            
            #1 if node j comes after node i
            V = {(i,j):s.addVar(vtype = GRB.BINARY) for i in NN for j in NN}
            
            #Conservation of flow
            OneEdgeOut = {i:s.addConstr(quicksum(V[i,j] for j in NN ) == 1) for i in NN}
            OneEdgeIn = {j:s.addConstr(quicksum(V[i,j] for i in NN ) == 1) for j in NN}
            
            CantUseNodesInK = {(i,j):s.addConstr(V[i,j] == 0) for (i,j) in K}
            s.setParam('OutputFlag',0)
            s.setParam("LazyConstraints",1)
            
            
            def CallbackSubCycle (model, where):
                if where == GRB.Callback.MIPSOL:
                    print("begining the subcycle elimination!")
                    
                    SubSol = []
                    Sub = {k: v for (k,v) in zip(V.keys(), model.cbGetSolution(list(V.values())))}
                    for k in Sub:
                        if Sub[k] > 0.9:
                            SubSol.append(k)
                    #Idea of improvement : better way to determine the factors of a hamiltonian circle

                    # Done is the set of squares already looked at
                    Done = set()
                    SubPaths = []
                    for s in SubSol:
                        
                        if s[0] not in Done:
                            # Find the path that starts at this square and store it in Path
                            Path = set()
                            currentNode = s[0]
                            
                            while currentNode not in Path:
                                
                                for s2 in SubSol:
                                    (f2,t2) = s2
                                    if s2[0] == currentNode:
                                        Path.add(currentNode)
                                        currentNode = s2[1]
                                
                            
                            if len(Path) < len(SubSol):
                                SubPaths.append(Path)
                            Done |= Path
                    
                    if len(SubPaths) > 0:
                        LongestSubCycleLength = 0
                        LongestSub = set()
                        
                        for i in SubPaths:
                            if len(i) > LongestSubCycleLength:
                                LongestSub = i
                                LongestSubCycleLength = len(i)
                        
                        model.cbLazy(quicksum(V[n1,n2] 
                                            for n1 in LongestSub for n2 in LongestSub
                                            if (n1,n2) in SubSol)<=LongestSubCycleLength-1)

            
            s.optimize(CallbackSubCycle)
        
            if s.status == GRB.INFEASIBLE:
                
                valueX = {}
                infeasible = []
                for d in G:
                    for b in BW:
                        if XV[b,d] > 0.9:
                            infeasible.append((b,d))
                            valueX[(b,d)] = XV[b,d]
    
    
                model.cbLazy(quicksum(Y[b,d,n] for b in BW for d in G for n in Num if (b,d,n) not in Ysol) + quicksum(1- Y[b,d,n] for (b,d,n) in Ysol) -1 >= 0)
                
            else:
                if s.status != GRB.INFEASIBLE:
                    Path = {}
                    for i in NN:
                        for j in NN:
                            if V[i,j].x > 0.9:
                                print("node "+ str(i) + " to node " + str(j))
                                Path[i] = j
                    keys = Path.keys()
                    
                    for i in keys:
                        start = i
                        break
                    
                    current = start
                    
                    Order = []
                    
                    for i in Path:
                        current = Path[current]
                        Order.append(current)
                        
                    print(Order)
                if queue != None:
                    queue.put("Feasible")
    # =============================================================================
    
    # =============================================================================
    
    
    
                
    m.setParam('LazyConstraints', 1)
    
    
    
    #while True:
    N = []
    m.optimize(Callback)

    if m.status == GRB.INFEASIBLE:
        print("no master solution")
        if queue != None:
            queue.put("Infeasible")
    else:
        if (isFeasible[0] == False):
            print(" no subproblem solutions")
                    #print("block " + str(b) + " starts on day " + str(d) + " " +str(X[b,d].x) + " times")
            if queue != None:
                queue.put("Infeasible")
        print("----------------------------------------")
        if queue != None:
            queue.put("feasible")

        # =============================================================================
        # =============================================================================
        
        
        
        
        #idea for better cuts:
            #1. given that we know the number of shift blocks WILL equal to the number
            # of day off blocks. We can do a warm start cut that ensures:
            # the number of total work offs days must be >= number of shift blocks x minimum day off length
            # Vice Versa, check: number of t total work offs <= number of shift blocks x maximum day oof length
            
            
            # 2. symmetry breaking. If one master problem is infeasible, then its rotations/ shifts that preserves the same order
            #is also infeasible. Hence, CUT
            #
            #