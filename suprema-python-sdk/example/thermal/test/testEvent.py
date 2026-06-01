import grpc
import datetime
import threading

EVENT_QUEUE_SIZE = 16

class TestEvent:
  eventSvc = None
  eventCh = None
  thermalSvc = None
  firstEventID = 0

  def __init__(self, eventSvc, thermalSvc): 
    self.eventSvc = eventSvc
    self.thermalSvc = thermalSvc
    
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

  def test(self, deviceID):
    try:
      print(f'\n===== Log Events with Temperature =====\n', flush=True)

      events = self.thermalSvc.getTemperatureLog(deviceID, self.firstEventID, 0)
      for event in events:
        self.printEvent(event)

    except grpc.RpcError as e:
      print(f'Cannot get temperature logs: {e}', flush=True)
      raise   

  def printEvent(self, event):
    try:
      if int(event.userID) == 0xffffffff: # no user ID
        print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}, Temperature {event.temperature}', flush=True)
      else:
        print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}, Temperature {event.temperature}', flush=True)
    except ValueError: # invalid user ID
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}, Temperature {event.temperature}', flush=True)

    