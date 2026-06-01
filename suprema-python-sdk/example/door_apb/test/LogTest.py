import grpc
import datetime
import threading


EVENT_QUEUE_SIZE = 16
MAX_NUM_OF_LOG = 32

FIRST_DOOR_EVENT = 0x5000 # BS2_EVENT_DOOR_UNLOCKED
LAST_DOOR_EVENT = 0x5E00 # BS2_EVENT_DOOR_UNLOCK

class LogTest:
  eventSvc_ = None
  eventCh = None

  def __init__(self, eventSvc): 
    self.eventSvc_ = eventSvc
    
  def handleEvent(self):
    try:
      for event in self.eventCh:
        self.printEvent(event)
    
    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Monitoring is cancelled', flush=True)    
      else:
        print(f'Cannot get realtime events: {e}') 

  def startMonitoring(self, deviceID):
    try:
      self.eventSvc_.enableMonitoring(deviceID)
      self.eventCh = self.eventSvc_.subscribe(EVENT_QUEUE_SIZE)

      statusThread = threading.Thread(target=self.handleEvent)
      statusThread.start()

    except grpc.RpcError as e:
      print(f'Cannot start monitoring: {e}', flush=True) 
      raise   

  def stopMonitoring(self, deviceID):
    try:
      self.eventSvc_.disableMonitoring(deviceID)
      self.eventCh.cancel()

    except grpc.RpcError as e:
      print(f'Cannot stop monitoring: {e}', flush=True) 
      raise

  def printEvent(self, event):
    if event.eventCode >= FIRST_DOOR_EVENT and event.eventCode <= LAST_DOOR_EVENT:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Door {event.entityID}, {self.eventSvc_.getEventString(event.eventCode, event.subCode)}', flush=True)
    else:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc_.getEventString(event.eventCode, event.subCode)}', flush=True)
