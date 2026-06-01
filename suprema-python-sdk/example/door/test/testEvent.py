import grpc
import datetime
import threading
import event_pb2

EVENT_QUEUE_SIZE = 16
MAX_NUM_OF_LOG = 32

FIRST_DOOR_EVENT = 0x5000 # BS2_EVENT_DOOR_UNLOCKED
LAST_DOOR_EVENT = 0x5E00 # BS2_EVENT_DOOR_UNLOCK

class TestEvent:
  eventSvc = None
  eventCh = None
  firstEventID = 0

  def __init__(self, eventSvc): 
    self.eventSvc = eventSvc
    
  def handleEvent(self):
    try:
      for event in self.eventCh:
        if self.firstEventID == 0:
          self.firstEventID = event.ID
        self.printEvent(event)
    
    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Monitoring is cancelled', flush=True)    
      else:
        print(f'Cannot get realtime events: {e}') 

  def startMonitoring(self, deviceID):
    try:
      self.eventSvc.enableMonitoring(deviceID)
      self.eventCh = self.eventSvc.subscribe(EVENT_QUEUE_SIZE)

      statusThread = threading.Thread(target=self.handleEvent)
      statusThread.start()

    except grpc.RpcError as e:
      print(f'Cannot start monitoring: {e}', flush=True) 
      raise   

  def stopMonitoring(self, deviceID):
    try:
      self.eventSvc.disableMonitoring(deviceID)
      self.eventCh.cancel()

    except grpc.RpcError as e:
      print(f'Cannot stop monitoring: {e}', flush=True) 
      raise

  def getUserID(self, deviceID):
    try:
      events = self.eventSvc.getLog(deviceID, self.firstEventID, MAX_NUM_OF_LOG)

      for event in events:
        if event.eventCode == 0x1900: # BS2_EVENT_ACCESS_DENIED
          return event.userID

      return None

    except grpc.RpcError as e:
      print(f'Cannot get user ID: {e}', flush=True) 
      raise

  def printEvent(self, event):
    if event.eventCode >= FIRST_DOOR_EVENT and event.eventCode <= LAST_DOOR_EVENT:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Door {event.entityID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)
    else:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)

    