import grpc
import datetime
import threading
import event_pb2

EVENT_QUEUE_SIZE = 16

FIRST_APB_EVENT = 0x6000 # BS2_EVENT_ZONE_APB_VIOLATION
LAST_APB_EVENT = 0x6200 # BS2_EVENT_ZONE_APB_ALARM_CLEAR

class TestEvent:
  eventSvc = None
  eventCh = None

  def __init__(self, eventSvc): 
    self.eventSvc = eventSvc
    
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

  def printEvent(self, event):
    if event.eventCode >= FIRST_APB_EVENT and event.eventCode <= LAST_APB_EVENT:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: APB Zone {event.entityID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)
    else:
      print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)

    