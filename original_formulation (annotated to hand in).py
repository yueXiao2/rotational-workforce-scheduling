from gurobipy import *
from fileReader import *

#==================DATA READING===============================================
Path = "testcases/Example"
fileNum = 1
file = Path + str(fileNum) + ".txt"
dataMap = read_data(file)
print(file)

planningLength = dataMap['scheduleLength']
G = range(planningLength)

numEmployee = dataMap['numEmployees']
E = range(numEmployee)

schedulingLength = planningLength * numEmployee
D = range(schedulingLength)

# S = [0,1,2] 0: morning, 1:afternoon, 2:night
shiftType = []
for day in ['morning', 'afternoon', 'night']:
    if dataMap[day] != []:
        shiftType.append(dataMap[day][0])
S = range(dataMap['numShifts'])

#T[s][d] - statff requirementsfor shift s in day d
workDemand = dataMap['matrix']

minD = dataMap['minDaysOffLength']
maxD = dataMap['maxDaysOffLength']
minWork = dataMap['minWorkBlockLength']
maxWork = dataMap['maxWorkBlockLength']

# min[s] = minimum length of consecutive shifts s
# max defined similarly
minShift = []
maxShift = []
for day in ['morning', 'afternoon', 'night']:
    if dataMap[day] != []:
        minShift.append(dataMap[day][1])
        maxShift.append(dataMap[day][2])

# e.g. ['N','M']
F2 = dataMap['notAllowedShiftSequences2']

# e.g. ['N','M'] means 'N' cannot be followed by 'M' with day off in between
F3 = dataMap['notAllowedShiftSequences3']

#=========================LP MODEL============================================
m = Model('RWS')

#Varibles
# 1 if shift s on day d is part of the working schedule
X = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in D}

# 1 if a sequence of minWork shift starts on day d
Y = {d:m.addVar(vtype = GRB.BINARY) for d in D}

# 1 if a sequence of minShift for shift s starts on day d
Z = {(s,d):m.addVar(vtype = GRB.BINARY) for s in S for d in D}

# every shift requirement on anyday must be covered exactly
shiftConverage = {(s,d):m.addConstr(
        quicksum( X[s,dd] for dd in D if (dd % planningLength) == d) == workDemand[s][d]) 
        for s in S for d in G}

# at least one shift has to be scheduled for every (maximum day off length + 1) days
maxDayOffs = {d:m.addConstr(quicksum(X[s,dd] for s in S for dd in range(d,min((d+maxD+1),len(D)))) >= 1) 
                                for d in D}

# if no shift on day d, then there must be at least one shift on day d-1 or day d+1. This is for minD = 2
if (minD > 1):
    minDayOffs = {d:m.addConstr(1 - quicksum(X[s,d] for s in S) <= 2 - quicksum((X[s,d-1] + X[s,d+1]) for s in S)) 
                                                for d in D if (d > 0 and d < schedulingLength-1)}

# no consecutive shifts exceed the length of maxWork
maxWorkDays = {d:m.addConstr(quicksum(X[s,dd] for s in S for dd in range(d,min(d+maxWork+1,len(D)))) <= maxWork) 
                                            for d in D}

#  y[d] = 1 if a number of minWork are scheduled on days {d,...,d+minWork-1}
minWorkDays = {d:m.addConstr(Y[d]<= (quicksum(X[s,dd] for s in S for dd in range(d,min(d+minWork,len(D))))/minWork)) 
                                for d in D}

# every shift is part of a shift block that respects the minimum length
shiftSequence = {(s,d):m.addConstr(X[s,d+minWork-1] <= quicksum( Y[dd] for dd in range(d,d+minWork))) 
                    for s in S for d in D if d < schedulingLength - minWork}

# no consecutive shifts listed in F2. 
#If previous day contains shift s1, 
#then the next day cannot have s2 such that (s1,s2) in F2 
if len(F2) > 0:
    forbidden2 = {(f,d):m.addConstr(X[shiftType.index(F2[f][0]),d] <= 1 - X[shiftType.index(F2[f][1]),d+1]) for f in range(len(F2)) 
                    for d in D if d < schedulingLength-1}

# no forbidden shifts listed in F3. 
#If the first day contains shift s1, second day is a day off, 
#then the third day cannot be s2 such that (s1,s2) in F3
if len(F3) > 0:
    forbidden3 = {(f,d):m.addConstr(
            X[shiftType.index(F3[f][0]),d] 
            <= 1 + quicksum(X[s,d+1]  
            for s in S) - X[shiftType.index(F3[f][1]),d+2])
            for f in range(len(F3)) for d in D if d < schedulingLength - 2}

#at most one shift can be worked per day for anyone
OneShiftPerDay = {d:m.addConstr(quicksum(X[s,d] for s in S) <=1) for d in D}

# no consecutive shifts s exceeds the maixmum length for that shift s
MaxLengthShift = {(s,d):m.addConstr(quicksum( X[s,dd] for dd in range(d,min(d+maxShift[s]+1,len(D))))<=maxShift[s]) 
                        for s in S for d in D}


# no consecutive shifts s is less than the minimum length for that shift s
MinLengthShift1 = {(s,d):m.addConstr(Z[s,d] <= (quicksum(X[s,dd] for dd in range(d,min(d+minShift[s],len(D)-1)))/minShift[s])) 
            for s in S for d in D}

minLengthShift2 = {(s,d):m.addConstr( X[s,d+minShift[s]-1] <= quicksum(Z[s,dd] for dd in range(d,d+minShift[s])))
                    for s in S for d in D if d < schedulingLength - minShift[s]}


m.optimize()

if m.status == GRB.INFEASIBLE:
    print("infeasible problem")
else:
    
    # nice output formatting
    outputStr = ""
    for d in D:
        
        if d % planningLength == 0 and d != 0:
            outputStr += "\n"
        count = 0    
        for s in S:
          if X[s,d].x > 0.9:
              outputStr += " " +shiftType[s] +" "
          else:
              count += 1
              if count == 3:
                  outputStr += " - "

    print(outputStr)