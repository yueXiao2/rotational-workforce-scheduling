from gurobipy import *
from fileReader import *


#=================DATA READING================================================
# the string name of the file
# *MODEIFY THIS TO YOUR OWN FILE DIRECTORY*
file = "testcases/Example"

# the test intance number to choose
num = 1869

# a map that contains all the necessary data
dataMap = read_data(file+str(num)+".txt")

#length of planning horizon. e.g. a week (7 days)
planningLength = dataMap['scheduleLength']
G = range(planningLength)


numEmployee = dataMap['numEmployees']
E = range(numEmployee)

#length of the whole scheduling
schedulingLength = planningLength * numEmployee
D = range(schedulingLength)

# S = ['D','A','N']
shiftType = []
for day in ['morning', 'afternoon', 'night']:
    if dataMap[day] != []:
        shiftType.append(dataMap[day][0])

# mornining = 0, afternoon = 1, night = 2
S = range(dataMap['numShifts'])

# T[s][d]
workDemand = dataMap['matrix']

#min/max consecutive day offs
minD = dataMap['minDaysOffLength']
maxD = dataMap['maxDaysOffLength']

#min/max consecutive working days
minWork = dataMap['minWorkBlockLength']
maxWork = dataMap['maxWorkBlockLength']

# min/max consecutive working days of each shift
# index 0 - for Morning
# index 1 - for Afternoon
# index 2 - for Night
# e.g.[1,2,3]
minShift = []
maxShift = []
for day in ['morning', 'afternoon', 'night']:
    if dataMap[day] != []:
        minShift.append(dataMap[day][1])
        maxShift.append(dataMap[day][2])

       
# forbidden consecutive shifts
# e.g. F2[0] = ['N','M'] - a night shift is not allowed to follow by a morning
F2 = dataMap['notAllowedShiftSequences2']

# forbidden consecutive shifts with one day off in between
# e.g. ['N','A'] - a night shift following by a day off and then afternoon is not allowed
F3 = dataMap['notAllowedShiftSequences3']

#==================COMPUTIING THE SET OF FEASIBLE SHIFT BLOCKS B===============

# a list of feasible working blocks
B = []

DW = range(maxWork)

# current length of work block we are currently looking for 
L = minWork

# Find all feasible working blocks given a fixed length L
# and enumerate over all possible L
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
        ForbiddenSequence2 = {(f): m.addConstr(X[shiftType.index(F2[f][0]),d] + X[shiftType.index(F2[f][1]),d+1] <= 1) 
        for d in DW if d < maxWork-1 
        for f in range(len(F2))}
        
    # the length of the block must of length L    
    Length = m.addConstr(quicksum(X[s,d] for s in S for d in DW) == L)
    
    # shift blocks must be continous witout day off in between.
    #lowerbound on shfit block (e.g. the days that below the length L must have one shift)
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
        
        # no-good cut/ rubbish cut: cuts off the discovered solutions in the set W
        newSolution = {b:m.addConstr(quicksum(X[s,d] for s in S for d in range(len(b)) if s != b[d]) 
                                    + quicksum(1 - X[b[d],d] for d in range(len(b))) >= 1) 
            for b in B if len(b) == L}
    
    m.optimize()
    
    # increment L if all solutions of the current L are found
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

print("there are ",len(B),"shift blocks in total")


#====================USEFUL FUNCTIONS========================================
#Computes the converage of a shift block b starting on day d
#return: list of shifts s in day g that are covered
def Coverage(b,d):
    """
    computes the converage of a shift block b starting on day d
        parameters:
            b - a shift block in set B
            d - starting day
        return:
            a set of shifts s on day d that are covered
    """
    
    currentDay = d
    coverageList = []
    
    for i in b:

        coverageList.append((i,currentDay))
        currentDay = (currentDay + 1) % planningLength
    
    return coverageList


#given the shift s in day d that is needed to be covered
#return the shift block b staring on day g that is able to cover this
def C(s,d):
    """
    given the shift s in day d that is needed to be covered, computes the
    shift block b staring on day g that is able to cover this
    
    parameter:
        s - shift type
        d - day d in the week
    return:
        a set of shift blocks b starting on day d that can cover (s,d)
    
    """
    CList = []
    for g in G:
        for b in B:
            if (s,d) in Coverage(b,g):
                CList.append(tuple([b,g]))
    return CList


def maxNumBlocks():
    """
    Computes the upperbound of how many shift blocks can there be in a schedule
    """
    minLengthBlock = minWork + minD
    
    maxNum = (schedulingLength) / minLengthBlock
    
    return int(maxNum)

def additionEmp (n1, n2):
    """
    Calculates how many additional employees are needed if node n1 connects to
    node n2
    
        parameter:
            n1 - the first node
            n2 - the second node
        return:
            additionalCount - number of employees needed
    """
    additionCount = 0
    
    shiftBlock1 = n1[0]
    shiftBlock2 = n2[0]
    
    #first day of the block
    startDay1 = n1[1]
    startDay2 = n2[1]
    
    #length of the shift block
    blockLeng1 = len(shiftBlock1)
    blockLeng2 = len(shiftBlock2)
    
    #last day of the block
    blockEnd1 = startDay1 + blockLeng1 - 1
    blockEnd2 = startDay2 + blockLeng2 - 1
    
    #if the first block goes beyond the end of the week, 
    #we need an additional employee to take the exceeding part 
    if blockEnd1 > planningLength - 1:
        additionCount += 1
 
    #if the second block is to be started before or during the first block
    #we need an additional employee to take the second block
    if blockEnd1 % planningLength >= startDay2:
        additionCount += 1

    #if the second block goes beyond the end of the week, 
    #we need an additional employee to take the exceeding part    
    if blockEnd2 > planningLength - 1:
        additionCount += 1
    
    return additionCount

def cantUseNodes(N):
    """
    Given a set of nodes N, computes the combination of nodes that cannot be 
    following each other. e.g. if this returns (n1,n2) means that node n1 
    cannot be before node n2.
    
    This function is for the subproblem
    
    parameter:
        N - set of nodes to check
    return:
        list of tuples that indicate forbidden orderings
    """
    cantUse = []
    for n1 in range(len(N)):
        for n2 in range(len(N)):
            
            if(n1 == n2):
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
                continue
            
            shiftBlock1 = N[n1][0]
            shiftBlock2 = N[n2][0]
    
            #first day of the block
            startDay1 = N[n1][1]
            startDay2 = N[n2][1]
    
            #length of the shift block
            blockLeng1 = len(shiftBlock1)
            blockLeng2 = len(shiftBlock2)
    
            #last day of the block
            blockEnd1 = (startDay1 + blockLeng1 - 1) % planningLength
            blockEnd2 = (startDay2 + blockLeng2 - 1) % planningLength

            
            # the number of day offs between the last day of block1 and first day of block2
            offwork = startDay2 - blockEnd1 - 1
            
            # if the second block is worked by another employee, the offwork interval
            # goes over to the next week
            if blockEnd1 >= startDay2:
                offwork += 7

            # check if the offwork lengths satisfy the max and min lengths
            if offwork < minD or offwork > maxD:
                if (n1,n2) not in cantUse:
                    cantUse.append((n1,n2))
            
            # check forbidden sequence of length 3
            if len(F3) > 0 and offwork == 1:
                for i in F3:
                    if shiftBlock1[blockLeng1 - 1] == shiftType.index(i[0]) and shiftBlock2[0] == shiftType.index(i[1]):
                        if (n1,n2) not in cantUse:
                            cantUse.append((n1,n2))
    return cantUse


def Output(order, N):
    """
    Creates a nice looking output!
    
        parameter:
            order - list of nodes in order in the schedule
            N - list of nodes
    """
    outputString = ""
    scheduleMatrix = []
    
    


    
    for e in E:
        scheduleMatrix.append([])
        for d in G:
            scheduleMatrix[e].append(-1)
    
    currentEmp = 0
    for o in order:
        shiftBlock = N[o][0]
        startDay = N[o][1]
        
        currentDay = startDay

        for i in shiftBlock:
            scheduleMatrix[currentEmp][currentDay] = i
            currentDay += 1

            
            if currentDay > 6:
                currentEmp = (currentEmp + 1) % numEmployee
                currentDay = 0
        
        
            
    shiftString = ''
    for e in E:
        for d in G:
            currentShift = scheduleMatrix[e][d]
            
            
            if currentShift == 3:
                shiftString += ' - '
            else:
                shiftString += " "+ shiftType[currentShift] + " "
            
            outputString +=shiftString
    
        if e < numEmployee - 1:
            shiftString += "\n"
    
    return shiftString

#========================MASTER PROBLEM=======================================
# the possible number of times that the same block on the same day can be used
Num = range(1,maxNumBlocks()+1)
print("master problem")
m = Model("master problem")

# the number of times that block b starts on day d
X = {(b,d):m.addVar(vtype = GRB.INTEGER) for b in B for d in G}

# 1 if block d starts on day d n times
# if all Y's 0 for a particular (b,d), then it is not used at all
Y = {(b,d,n):m.addVar(vtype = GRB.BINARY) for b in B for d in G for n in Num}

# make sure that the blocks used exactly satisfy the shift demand for every shift s and everyy day of the week d
DemandRequirement = {(s,d):m.addConstr(quicksum(X[b,g] for (b,g) in X if (b,g) in C(s,d)) == workDemand[s][d]) for s in S for d in G}

# linking X and Y together.
LinkXAndY = {(b,d):m.addConstr(X[b,d] == quicksum(Y[b,d,n] * n for n in Num)) 
                    for (b,d) in X}

# at most one Y is allowed. all Y's are 0 means that a block is not used
OneY = {(b,d):m.addConstr(quicksum(Y[b,d,n] for n in Num) <= 1) for (b,d) in X}


#warm up initial cut: given the number of shift blocks == number of off blocks, for a feasible solution to occur, it is necessarily that 
# the totak day offs >= the number of day off blocks * minimal length of day off block
#total day offs  = schedule length - total shift days
WarmUpLowerCut = m.addConstr(schedulingLength - quicksum( X[b,d] * len(b) for d in G for b in B) >= quicksum(X[b,d] for d in G for b in B) * minD)
    
    
#warm up initial cut: given the number of shift blocks == number of off blocks, for a feasible solution to occur, it is necessarily that 
# the totak day offs <= the number of day off blocks * maximum length of day off block
#total day offs  = schedule length - total shift days
WarmUpUpperCut = m.addConstr(schedulingLength - quicksum( X[b,d] * len(b) for d in G for b in B) <= quicksum(X[b,d] for d in G for b in B) * maxD)


m.setParam('OutputFlag',0)
m.setParam("LazyConstraints",1)
m.setParam('Threads',1)

# set of all the master problems we found
SolutionSet = []

# are there feasible subproblem solutions?
isFeasible = True

def CallBack(model, where):
    if where == GRB.Callback.MIPSOL:
        print("beginning the call back!")
        
        # retrive the solution from the master probelm: Y[b,d,n]
        YV = {k: v for (k,v) in zip(Y.keys(), model.cbGetSolution(list(Y.values()))) if v > 0.9}
        

                
        # check if this master problem has been found before
        if YV.keys() not in SolutionSet:
            SolutionSet.append(YV.keys())
            print("master solution appended. current length: " + str(len(SolutionSet)))
        else:
            global isFeasible
            print("terminated because encountered a previous master probelm solution")
            isFeasible = False
            model.terminate()
            return
            
        #============================SUBPROBELM==================================
        N = []
        # append each block used in the master problem as a node
        # the (b,d) that is used n times will count as n different nodes
        for k in YV:
            for i in range(k[2]):
                N.append((k[0],k[1])) 
                
                
        # a set of nodes that cannot be connected
        K = cantUseNodes(N)
        NN = range(len(N))
        
        s = Model("subproblem")
    
        # 1 if node i is connected to node j
        V = {(i,j):s.addVar(vtype = GRB.BINARY) for i in NN for j in NN if (i,j) not in K}
        
        # the total additional employees needed will equal to the total number of employees
        EmployeeNum = s.addConstr(quicksum(additionEmp(N[i],N[j])*V[i,j] for (i,j) in V) == numEmployee)
        
        #Conservation of flow
        OneEdgeOut = {i:s.addConstr(quicksum(V[i,j] for j in NN if (i,j) in V) == 1) for i in NN for v in V if v[0] == i}
        OneEdgeIn = {j:s.addConstr(quicksum(V[i,j] for i in NN if (i,j) in V) == 1) for j in NN for v in V if v[1] == j}   

        
        s.setParam('OutputFlag',0)
        s.setParam("LazyConstraints",1)
        
        def CallbackSubCycle (model, where):
            if where == GRB.Callback.MIPSOL:
                print("beginning the subcycle elimination!")
                
                SubSol = []
                Sub = {k: v for (k,v) in zip(V.keys(), model.cbGetSolution(list(V.values()))) if v > 0.9}
                for k in Sub:
                    SubSol.append(k)

                # computes the path of nodes
                Done = set()
                SubPaths = []
                for s in SubSol:
                    
                    if s[0] not in Done:
                        
                        # Find the path that starts at this node and store it in Path
                        Path = set()
                        currentNode = s[0]
                        
                        while currentNode not in Path:
                            
                            for s2 in SubSol:
                                (f2,t2) = s2
                                if s2[0] == currentNode:
                                    Path.add(currentNode)
                                    currentNode = s2[1]
                            
                        # if we found a cycle that does not use all the nodes,
                        # store it
                        if len(Path) < len(SubSol):
                            SubPaths.append(Path)
                        Done |= Path
                
                # if there is at least one subcycle
                # cut them off from the current subproblem solution
                if len(SubPaths) > 0:
    
                    for sub in SubPaths:
                        model.cbLazy(quicksum(V[n1,n2] 
                                            for n1 in sub for n2 in sub
                                            if (n1,n2) in SubSol)<= len(sub) - 1)

        s.optimize(CallbackSubCycle)
        
        # if an asscioated sub problem is not feasible,
        # then cut off this particular master problem solution
        if s.status == GRB.INFEASIBLE:
            # no good cut
            model.cbLazy(quicksum(Y[k] for k in Y if k not in YV) + quicksum(1- Y[k] for k in YV) -1 >= 0)
            
        else:
            
            # if sub problem is feasible,
            # SOLUTION FOUND
            if s.status != GRB.INFEASIBLE:
                Path = {}
                for (i,j) in V:
                    if V[i,j].x > 0.9:
                        Path[i] = j
                keys = Path.keys()
                
                #print statement formatting
                for i in keys:
                    start = i
                    break
                
                current = start
                
                Order = []
                
                for i in Path:
                    current = Path[current]
                    Order.append(current)    
                
                matrix = Output(Order,N)
                print(matrix)

m.optimize(CallBack)

if m.status == GRB.INFEASIBLE:
    print("no feasible master solution")
else:
    if isFeasible == False:
        print("no feasible sub solution")
