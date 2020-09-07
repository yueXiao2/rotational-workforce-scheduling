from gurobipy import *

planningLength = 7
G = range(planningLength)

numEmployee = 9
E = range(numEmployee)

schedulingLength = planningLength * numEmployee
D = range(schedulingLength)

shiftType = ["D","A","N"]
S = range(len(shiftType))

workDemand = [[2,2,2,2,2,2,2],
              [2,2,2,2,2,2,2],
              [2,2,2,2,2,2,2]]

minD = 2
maxD = 4
minWork = 4
maxWork = 7
minShift = [2,2,2]
maxShift = [7,6,4]

F2 = [['N','D'],
      ['N','A'],
      ['A','D']]

#F3

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

            
    




