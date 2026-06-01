import grpc
import datetime
import threading

EVENT_QUEUE_SIZE = 16

class TestEvent:
  eventSvc = None
  eventCh = None
  tnaSvc = None
  firstEventID = 0

  def __init__(self, eventSvc, tnaSvc): 
    self.eventSvc = eventSvc
    self.tnaSvc = tnaSvc
    
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
      print(f'\n===== TNA Log Events =====\n', flush=True)

      events = self.tnaSvc.getTNALog(deviceID, self.firstEventID, 0)
      config = self.tnaSvc.getConfig(deviceID)

      for event in events:
        self.printEvent(event, config)

    except grpc.RpcError as e:
      print(f'Cannot get T&A logs: {e}', flush=True)   
      raise

  def printEvent(self, event, config):
    print(f'{datetime.datetime.utcfromtimestamp(event.timestamp)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc.getEventString(event.eventCode, event.subCode)}, {self.getTNALabel(event.TNAKey, config)} ', flush=True)

  def getTNALabel(self, key, config):
    if len(config.labels) > key - 1:
      return "%s(Key_%d)" % (config.labels[key - 1], key)
    else:
      return "Key_%s" % key



    