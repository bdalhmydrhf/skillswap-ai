import grpc
import threading
import datetime

QUEUE_SIZE = 16
MAX_NUM_OF_LOG = 16384

class EventMgr:
  eventSvc = None
  testConfig = None

  eventCh = None
  
  def __init__(self, eventSvc, testConfig): 
    self.eventSvc = eventSvc
    self.testConfig = testConfig

  def handleEvent(self, callback):
    try:
      self.eventCh = self.eventSvc.subscribe(QUEUE_SIZE)
      statusThread = threading.Thread(target=self.receiveEvent, args=(callback,))
      statusThread.start()
    except grpc.RpcError as e:
      print(f'Cannot subscribe to the event monitoring channel: {e}')   

  def receiveEvent(self, callback):
    try:
      for event in self.eventCh:
        if not (callback is None):
          callback(event)
        else:
          print(f'\nEvent: {event}', flush=True)
    
    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Monitoring is cancelled', flush=True)    
      else:
        print(f'Cannot get realtime events: {e}') 

  def readNewLog(self, devInfo, maxNumOfLog):
    try:
      eventLogs = self.eventSvc.getLog(devInfo['device_id'], devInfo['last_event_id'] + 1, maxNumOfLog)

      if len(eventLogs) > 0:
        self.testConfig.updateLastEventID(devInfo['device_id'], eventLogs[len(eventLogs) - 1].ID)

      return eventLogs

    except grpc.RpcError as e:
      print(f'Cannot read new events: {e}')         

  def handleConnection(self, deviceID):
    print(f'***** Device {deviceID} is connected', flush=True)
    try:
      dev = self.testConfig.getDeviceInfo(deviceID)
      if dev is None:
        print(f'!!! Device {deviceID} is not in the configuration file', flush=True)

      eventLogs = []

      while True:
        print(f"[{deviceID}] Reading log records starting from {dev['last_event_id']}...", flush=True)
        newLogs = self.readNewLog(dev, MAX_NUM_OF_LOG)
        print(f'[{deviceID}] Read {len(newLogs)} events', flush=True)
        eventLogs.extend(newLogs)

        # check if read the last log
        if len(newLogs) < MAX_NUM_OF_LOG:
          break

      # do something with the event logs
      # ...
      print(f'[{deviceID}] The total number of new events: {len(eventLogs)}', flush=True)

      # enable real-time monitoring
      self.eventSvc.enableMonitoring(deviceID)
    except grpc.RpcError as e:
      print(f'Cannot enable monitoring: {e}')   

  def printEvent(self, event):
    print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}', flush=True)
    