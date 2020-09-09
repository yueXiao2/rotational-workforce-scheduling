def next_valid_line(f):
    # skip comments and empty lines, return None on EOF
    while True:
        line = f.readline()
        if len(line) == 0:
            return None
        if len(line) > 1 and line[0] != '#':
            return line.strip()

def read_data(input_file):
    
    file = open(input_file, 'r')

    scheduleLength = int(next_valid_line(file))
    numEmployees = int(next_valid_line(file))
    numShifts = int(next_valid_line(file))
    
    matrixline1 = []
    matrixline2 = []
    matrixline3 = []
    for matrix in [matrixline1, matrixline2, matrixline3]:
        matrixTemp = next_valid_line(file).split()
        for num in matrixTemp:
            matrix.append(int(num))
    matrix = [matrixline1, matrixline2, matrixline3]
    
    morning = []
    afternoon = []
    night = []
    for day in [morning, afternoon, night]:
        dayTemp = next_valid_line(file).split()
        day.append(dayTemp[0])
        day.append(int(dayTemp[3]))
        day.append(int(dayTemp[4]))
        
    lengthTemp = next_valid_line(file).split()
    minDaysOffLength = int(lengthTemp[0]) 
    maxDaysOffLength = int(lengthTemp[1])
    
    lengthTemp = next_valid_line(file).split()
    minWorkBlockLength = int(lengthTemp[0]) 
    maxWorkBlockLength = int(lengthTemp[1])
    
    lengthTemp = next_valid_line(file).split()
    NrSequencesOfLength2 = int(lengthTemp[0]) 
    NrSequencesOfLength3 = int(lengthTemp[1])
    
    notAllowedShiftSequences2 = []
    notAllowedShiftSequences3 = []
    while (True):
        temp = next_valid_line(file)
        if temp == None:
            break
        temp = temp.split()
        if (len(temp) == 2):
            notAllowedShiftSequences2.append(temp)
        else:
            notAllowedShiftSequences3.append(temp)
        
    shitToMap = [scheduleLength, numEmployees, numShifts, matrix,
                morning, afternoon, night,
                minDaysOffLength, maxDaysOffLength, minWorkBlockLength,
                maxWorkBlockLength, NrSequencesOfLength2, NrSequencesOfLength3,
                notAllowedShiftSequences2, notAllowedShiftSequences3]
    dataMap = {}
    count = 0
    for key in ['scheduleLength', 'numEmployees', 'numShifts', 'matrix', 
                'morning', 'afternoon', 'night',
                'minDaysOffLength', 'maxDaysOffLength', 'minWorkBlockLength',
                'maxWorkBlockLength', 'NrSequencesOfLength2', 'NrSequencesOfLength3',
                'notAllowedShiftSequences2', 'notAllowedShiftSequences3']:
        dataMap[key] = shitToMap[count]
        count+=1
    return dataMap