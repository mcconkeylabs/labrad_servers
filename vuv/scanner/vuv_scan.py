import labrad
import labrad.units as U
from time import sleep

COUNT_MIN = 0
COUNT_MAX = 4775
PULSE_DELAY = U.Value(1, 'ms')

CH_LIST = ['MCS Start', 'MCS Advance', 'Stepper Advance', 'Stepper Direction']
MOVE_CHS = ['Stepper Advance', 'Stepper Direction']
CH_MAP = {'MCS Start' : 1,
          'MCS Advance' : 2,
          'Stepper Advance' : 3,
          'Stepper Direction' : 4}
          
PULSER_NAME = 'BNC Serial Server'
          
def initializePulser(pulser, don, doff):
    p = pulser.packet()
    
    #TODO: Change to dynamic name
    p.select_device(0)
    
    p.select_channel(CH_MAP['MCS Start'])
    p.state(True)
    p.width(U.Value(10, 'us'))
    p.delay(U.Value(0.0, 's'))
    p.mode('Single')
    p.polarity(True)
    p.output(False)
    
    p.select_channel(CH_MAP['MCS Advance'])
    p.state(True)
    p.width(U.Value(10, 'us'))
    p.delay(PULSE_DELAY)
    p.mode('DutyCycle', (don, doff))
    p.polarity(True)
    p.output(False)
    
    p.select_channel(CH_MAP['Stepper Advance'])
    p.state(True)
    p.width(U.Value(10, 'us'))
    p.delay(PULSE_DELAY)
    p.mode('Normal')
    p.polarity(True)
    p.output(False)
    
    p.select_channel(CH_MAP['Stepper Direction'])
    p.state(True)
    p.width(PULSE_DELAY * 4)
    p.delay(U.Value(0.0, 's'))
    p.mode('Normal')
    p.polarity(True)
    p.output(False)
    
    p.send()
    
def setMove(pulser, advs, period = U.Value(50, 'ms'), moveChsOnly = False):
    p = pulser.packet()
    
    #set move direction
    p.select_channel(CH_MAP['Stepper Direction'])
    p.polarity(advs > 0)
    
    if moveChsOnly:
        moveChs = [CH_MAP[x] for x in MOVE_CHS]
        p.enable(moveChs, True)
        print 'Enabling only channels {0}'.format(moveChs)
    
    #advances
    p.select_channel(0)
    p.mode('Burst', abs(advs) + 8)
    p.trigger_period(period)
    
    #now set stepper channel to move only advs number of channels
    p.select_channel(CH_MAP['Stepper Advance'])
    p.mode('Burst', abs(advs))
    p.send()
#    
#def scanPass(cxn, start, stop):
#    stepper = cxn['VUV Stepper Server']
#    pulser = cxn['BNC Serial Server']
#    
#    stepper.move_to(start - 1, 0, True)
#    stepper.move_to(start, 0, True)
#    
#    prepMCSChannels(cxn, 1, 7)
#    
#    stepper.move_to(stop, 0, False)
#    
#    pulser.select_device(0)
#    pulser.trigger_period(U.Value(0.5, 's'))
#    pulser.start()
    
def move(pulser, advs, dwell = U.Value(50, 'ms'), moveChsOnly = False):
    setMove(pulser, advs, dwell, moveChsOnly)
    print 'Setting move with {0} {1}'.format(advs, dwell)
    pulser.start()
    print 'Pulser started'
    while pulser.run_state():
        sleep(dwell['s'] / 2)
    
def scanPass(pulser, advs, dwell):

    #start with all channels enabled
    pulser.enable(CH_MAP.values())    
    #run pass
    move(pulser, advs, dwell)
        
    move(pulser, -(advs+8), moveChsOnly=True)
    move(pulser, 8, moveChsOnly=True)
    
    #restore pulser channels to preferred settings
    p = pulser.packet()
    p.select_channel(CH_MAP['Stepper Advance'])
    p.mode('Normal')
    p.select_channel(0)
    p.mode('Burst', 1000)
    p.send()
    
if __name__ == '__main__':
    cxn = labrad.connect()
    pulser = cxn['BNC Serial Server']
    pulser.select_device(0)
    
    for i in range(2):
        scanPass(pulser, 20, U.Value(0.25, 's'))
        