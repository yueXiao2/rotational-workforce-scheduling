from gurobipy import *
from fileReader import *
import time

def decomp_master(queue, file):
    if queue != None:
        queue.put("Time test")
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
    
    def DayCoverage(d):
        
        day = d % planningLength
        
        coverage = []
        for b in B:
            for g in G:
                blockLength = len(b)
                
                startDay = g
                
                endDay = (blockLength + g - 1) % planningLength
                
                if endDay <= startDay:
                    if day in range(startDay,planningLength) or day in range(endDay):
                        if (b,g) not in coverage:
                            coverage.append((b,g))
                else:
                    if day in range(startDay,endDay+1):
                        if (b,g) not in coverage:
                            coverage.append((b,g))
        return coverage
    
    def maxNumBlocks():
        minLengthBlock = minD + minWork
        
        maxNum = (schedulingLength) / minLengthBlock
        
        return int(maxNum)
    
    
    def cantUseNodes(N):
        cantUse = []
        for n1 in range(len(N)):
            for n2 in range(len(N)):
                
                if n1 == n2:
                    if (n1,n2) not in cantUse:
                        cantUse.append((n1,n2))                
                    
                
                
                shiftBlock1 = N[n1][0]
                shiftBlock2 = N[n2][0]
                
                blockLength1 = len(shiftBlock1)
                blockLength2 = len(shiftBlock2)
                
                startDay1 = N[n1][1]
                startDay2 = N[n2][1]
                
                dayOffIndex = shiftBlock1.index(3)
                
                EndDay1 = (startDay1 + blockLength1 - 1) % planningLength
                
                if startDay2 != (EndDay1 + 1) % planningLength:
                    if (n1,n2) not in cantUse:
                        cantUse.append((n1,n2))
                
                numDayOffs = blockLength1 - dayOffIndex
                
                if len(F3) > 0 and numDayOffs == 1:
                    for i in F3:
                        if shiftBlock1[dayOffIndex - 1] == shiftType.index(i[0]) and shiftBlock2[0] == shiftType.index(i[1]):
                            if (n1,n2) not in cantUse:
                                cantUse.append((n1,n2))
        return cantUse   
    
    Num = range(1,maxNumBlocks()+1)
    print("master problem")
    m = Model("master problem")
    
    X = {(b,d):m.addVar(vtype = GRB.INTEGER) for b in B for d in G}
    
    Y = {(b,d,n):m.addVar(vtype = GRB.BINARY) for b in B for d in G for n in Num}
    
    
    DemandRequirement = {(s,d):m.addConstr(quicksum(X[b,g] for (b,g) in X if (b,g) in C(s,d)) == workDemand[s][d]) for s in S for d in G}
    
    LinkXAndY = {(b,d):m.addConstr(X[b,d] == quicksum(Y[b,d,n] * n for n in Num)) for (b,d) in X}
    
    OneY = {(b,d):m.addConstr(quicksum(Y[b,d,n] for n in Num) <= 1) for (b,d) in X}
    print("last constraint  ")
    ExactLength = m.addConstr(quicksum(X[b,d] * len(b) for (b,d) in X) == schedulingLength)
    
    AtLeastOneFollowUp = {(b,d):m.addConstr( quicksum(X[bb,dd] for bb in B for dd in G if dd == (len(b)+d)%planningLength)>= X[b,d]) for b in B for d in G}
    
    #CoverageDays = {d: m.addConstr(quicksum(X[b,dd] for (b,dd) in DayCoverage(d)) == numEmployee) for d in G}
    
    
    m.setParam('OutputFlag',0)
    m.setParam("LazyConstraints",1)
    m.setParam('Threads',1)
    
    SolutionSet = []
    isFeasible = [True]
    def CallBack(model, where):
        if where == GRB.Callback.MIPSOL:
            print("beginning the call back!")
            
            #Y[b,d,n]
            YV = {k: v for (k,v) in zip(Y.keys(), model.cbGetSolution(list(Y.values()))) if v > 0.9}
            
            N = []
            
            for k in YV:
                for i in range(k[2]):
                    N.append((k[0],k[1]))
                    
                    
            if YV.keys() not in SolutionSet:
                    SolutionSet.append(YV.keys())
                    print("solution appended. current length: " + str(len(SolutionSet)))
            else:
                    print("ohhhhh cyclic!")
                    isFeasible[0] = False
                    model.terminate()
                    return
            
            K = cantUseNodes(N)
            
            NN = range(len(N))
            #appearanceCount = {n:0 for n in NN}
            
            #for k in K:
            #    (k1,k2) = k
                
            #    appearanceCount[k1] += 1
            
            #for k in appearanceCount:
            #    if appearanceCount[k] == len(N):
            #        model.cbLazy(quicksum(Y[k] for k in Y if k not in YV) + quicksum(1- Y[k] for k in YV) -1 >= 0)
            #        return
            
            s = Model("subproblem")
        
            V = {(i,j):s.addVar(vtype = GRB.BINARY) for i in NN for j in NN}
            
            #Conservation of flow
            OneEdgeOut = {i:s.addConstr(quicksum(V[i,j] for j in NN) == 1) for i in NN}
            OneEdgeIn = {j:s.addConstr(quicksum(V[i,j] for i in NN) == 1) for j in NN}
            
            ForbiddenNodes = {(i,j):s.addConstr(V[i,j] == 0) for i in NN for j in NN if (i,j) in K}
            
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
                        #model.cbLazy(quicksum(V[n1,n2] 
                        #                    for n1 in LongestSub for n2 in LongestSub
                        #                    if (n1,n2) in SubSol)<=LongestSubCycleLength-1)
        
                        for sub in SubPaths:
                            model.cbLazy(quicksum(V[n1,n2] 
                                                for n1 in sub for n2 in sub
                                                if (n1,n2) in SubSol)<= len(sub) - 1)
    
            s.optimize(CallbackSubCycle)
            
            if s.status == GRB.INFEASIBLE:
    
    
                model.cbLazy(quicksum(Y[k] for k in Y if k not in YV) + quicksum(1- Y[k] for k in YV) -1 >= 0)
                
            else:
                
                
                if s.status != GRB.INFEASIBLE:
                    Path = {}
                    for (i,j) in V:
                        if V[i,j].x > 0.9:
                            print("node "+ str(i) +":" + str(N[i])+ " to node " + str(j)+":"+str(N[j]))
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
                    
                    for i in Order:
                        print(N[i][0],":",N[i][1])
    
    m.optimize(CallBack)