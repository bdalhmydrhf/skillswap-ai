import grpc
import datetime
import threading
import event_pb2

from example.cli.input import UserInput

EVENT_QUEUE_SIZE = 16
MAX_NUM_EVENT = 32

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

  def test(self, deviceID):
    try:
      print(f'\n===== Event Test =====\n', flush=True)
      UserInput.pressEnter('>> Try to authenticate credentials to check real-time monitoring. And, press ENTER to read the generated event logs.\n')

      if self.firstEventID == 0:
        print(f'\n>> There is no new event. Just read {MAX_NUM_EVENT} event logs from the start.', flush=True)
      else:
        print(f'\n>> Read new events starting from {self.firstEventID}.', flush=True)

      events = self.eventSvc.getLog(deviceID, self.firstEventID, MAX_NUM_EVENT)
      for event in events:
        self.printEvent(event)

      if len(events) > 0 and self.firstEventID != 0:
        print(f'\n>> Filter with event code {events[0].eventCode}', flush=True)

        filter = event_pb2.EventFilter(eventCode=events[0].eventCode)
        events = self.eventSvc.getLogWithFilter(deviceID, self.firstEventID, MAX_NUM_EVENT, [filter])

        for event in events:
          self.printEvent(event)

    except grpc.RpcError as e:
      print(f'Cannot get event logs: {e}', flush=True)   
      raise

  def printEvent(self, event):
    print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)

    