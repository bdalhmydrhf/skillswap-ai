import grpc
import datetime
import threading
import event_pb2

EVENT_QUEUE_SIZE = 16

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
        print(f'\nEvent: {event}', flush=True)
    
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

  def test(self, deviceID, userID):
    try:
      print(f'\n===== Log Events of Test User =====\n', flush=True)

      filter = event_pb2.EventFilter(userID=userID)
      events = self.eventSvc.getLogWithFilter(deviceID, self.firstEventID, 0, [filter])

      for event in events:
        self.printEvent(event)

      print(f'\n===== Verify Success Events of Test User =====\n', flush=True)

      filter.eventCode = 0x1000 # BS2_EVENT_VERIFY_SUCCESS
      events = self.eventSvc.getLogWithFilter(deviceID, self.firstEventID, 0, [filter])

      for event in events:
        self.printEvent(event)      

    except grpc.RpcError as e:
      print(f'Cannot get user logs: {e}', flush=True)   
      raise

  def printEvent(self, event):
    print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)

    