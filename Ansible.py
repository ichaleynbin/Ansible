import random

def bitList(message):
    #Python list comprehension magic which translates an ACII string into a list of 0s and 1s
    #  which include leading zeros, such that each string character is always 8 bits. 
    return [int(x) for x in ''.join('{0:08b}'.format(ord(x), 'b') for x in message)]

def stringify(message):
    #Python list comprehension magic which translates back a list of 0s and 1s like generated in bitlist
    #  into the ASCII character values, and then joins them into one string for return.
    return ''.join([chr(int(''.join([str(x) for x in message])[i:i+8],2)) for i in range(0,len(message),8)])

class Pair:
    #Shared entangled pair

    def __init__(self):

        #Generate initial state of zero just so self.state exists for later calls.

        self.state = 0
        
        #self.state can be an integer value from 0 to 3, representing a circular arrangement 
        #  of the complex state spaces, such as 0 indexing for (+1,0), 1 for (0,-i), 2 for (-1,0), and 3 for (0,+i)
        #This allows us to do %2 actions later, both 0 and 2 are opposing each other, as well as 1 and 3.

    def getState(self, direction):
        #This is both the sending and receiving action: 
        #A measurement is being made in the axis determined by direction

        if (self.state%2 == direction):
            #If state is a modulo of two(0,2) and the direction picked is the "0" direction, OR
            #  state is not a modulo of two (1,3) and the direction picked is the "1" direction
            #  then we are measuring in the direction of the current state, state should not change.
            return self.state

        else:
            #The else statement means we are not measuring in the direction of current aligment, 
            #  thus we have a 50/50 chance of measuring either of the options we have.
            self.state = (random.choice([0,2])+direction)
            return self.state
        
class Transciever: 
    ##Box to house one of the entangled pairs
    #As a 180 degree rotation of index is enough to normalize the fact that an entangled
    #  pair of particles will have opposite spins, this will be assumed. When one is in any state,
    #  for example say the zero state, the other is in the two state, 1:3, etc. This is just a 180
    #  degree rotation.

    def __init__(self,entangledPair):
        #Initialization housekeeping to store the link pair and so that += and .append work later. 
        self.link = entangledPair
        self.Queue = []
        self.AllSends = []
        self.Results = []
        self.currentBit = 0

    def IO(self,repetition):
        #Transciever has been given the message to make an input/output measurement. 

        if repetition == 0:
            #This control implementation allows the transciever controller to handle precision,
            #  allowing the transciever to largely remain precision agnostic.

            try: self.currentBit = self.Queue.pop(0)
            #Try to get next bit in the queue
            except: self.currentBit = 0
            #No bit exists in queue, just default to zero. 

            self.AllSends.append(self.currentBit)
            #Append this bit to sent bits

        self.Results.append(self.link.getState(self.currentBit))
        #Measure the linked pair in one of the two directions, and append the measurement to results.

    def clearQueue(self):
        #Cleanup Code
        self.Queue = []

    def addToQueue(self,message):
        #Add a message to the queue of bits to send

        if type(message)==str:
            #Check to see if the message is of type string, and if it is, kindly convert it to bits properly
            self.Queue+= bitList(message)

        else:
            #It's not a string, so assume that it's a list of bits. Good luck and godspeed
            self.Queue+= message

    def comprehend(self,precision):
        #Comprehend the results of all IO actions in the record. Sent bits are necessary to 
        #  comprehend the resultant measurements, and there's some comprehension magic to find the flippers

        flippers = [len(set(self.Results[i+1:i+precision]))-1 for i in range(0,len(self.Results),precision)]
        #This takes all of the measurement results, and parses it based on precision. 
        # Each measurement was repeated `precision` number of times, so throw out the first measurement
        #  because it's impaced by the previous, and then see how many different measurement results exist(set).
        # If only one measurement exists, we were (probably)measuring in the same direction.
        # If two measurements exist, we were definitely measing in the other direction.
        # This means that len(set())-1 is equivalent to whether we need to flip the send bit or not.

        message = stringify(list(map(lambda x:x[0]^x[1],zip(self.AllSends,flippers))))
        # Zip together the sent bits with the flipper bits, then xor them together. 
        # Pass the result of that xor to stringify and get back the transmitted message. 

        self.AllSends = []
        self.Results = []
        #Clear sends and results to keep their parity when importing and reusing transcievers

        return message

class TranscieverController:
    # This class only exists as a high level abstraction of practical control methods.
    # TCs control precision with the value self.repeats, which is how the transcievers
    #   themselves know to pull a new value, as x==0 is the first in a series. 
    # Real life concerns on how to sync two transcievers are far from negligible, but will be ignored
    #   for this program, as they're largely practical concerns already solved by protocols like TCP/IP.

    def __init__(self,T1,T2,repeats):
        #Store access to transcievers 1 and 2, as well as storing the precision repetitions. 
        self.TSC1 = T1
        self.TSC2 = T2
        self.repeats = repeats

    def TransmitBit(self):
        #This signals for one bit to be fully transmitted, which requires `self.repeats` measurements
        
        for x in range(self.repeats):
            self.TSC1.IO(x)
            self.TSC2.IO(x)


FirstMessage = "First message wahoo"
SecondMessage = "Second Best aww"

if __name__=="__main__":

    #Create an entangled pair, then give it to two new transcievers. 
    entangleds = Pair() 
    Transciever1 = Transciever(entangleds)
    Transciever2 = Transciever(entangleds)

    for precision in range(3,20):
        #Check how this works at various levels of precision.

        TC = TranscieverController(Transciever1,Transciever2,precision)
        #New Transciever controller of current precision. 

        Transciever1.addToQueue(FirstMessage)
        Transciever2.addToQueue(SecondMessage)
        #Give both transcievers their respective messages to send. 

        for _ in range(8*max(len(FirstMessage),len(SecondMessage))):
            # Transmit bits as many times as we need. 
            # Turns out it's 8 bits for every character in the longest message.
            TC.TransmitBit()
            
        # Bits are now transmitted, decode and print. 

        print(f"\n\nAt Precision {precision}, messages received were:")
        print(f"sent    : {SecondMessage}")
        firstRec = Transciever1.comprehend(precision)
        print(f"recieved: {firstRec}")
        print(f"sent    : {FirstMessage}")
        secondRec = Transciever2.comprehend(precision)
        print(f"recieved: {secondRec}")