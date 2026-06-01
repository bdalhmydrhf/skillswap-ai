import grpc
import json
import sys

import event_pb2_grpc
import event_pb2


class EventSvc:
  stub = None
  codeMap = None

  def __init__(self, channel): 
    try:
      self.stub = event_pb2_grpc.EventStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the event stub: {e}')
      raise

  def getLog(self, deviceID, startEventID, maxNumOfLog):
    try:
      response = self.stub.GetLog(event_pb2.GetLogRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog))
      return response.events
    except grpc.RpcError as e:
      print(f'Cannot get the event log: {e}')
      raise

  def getLogWithFilter(self, deviceID, startEventID, maxNumOfLog, filters):
    try:
      response = self.stub.GetLogWithFilter(event_pb2.GetLogWithFilterRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog, filters=filters))
      return response.events
    except grpc.RpcError as e:
      print(f'Cannot get the event log: {e}')
      raise

  def getImageLog(self, deviceID, startEventID, maxNumOfLog):
    try:
      response = self.stub.GetImageLog(event_pb2.GetImageLogRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog))
      return response.imageEvents
    except grpc.RpcError as e:
      print(f'Cannot get the image events: {e}')
      raise

  def clearLog(self, deviceID):
    try:
      self.stub.ClearLog(event_pb2.ClearLogRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot clear event log: {e}')
      raise

  def getImageLogFilter(self, deviceID):
    try:
      response = self.stub.GetImageFilter(event_pb2.GetImageFilterRequest(deviceID=deviceID))
      return response.filters
    except grpc.RpcError as e:
      print(f'Cannot get the ImageLog Filter: {e}')
      raise

  def setImageLogFilter(self, deviceID, filters):
    try:
      self.stub.SetImageFilter(event_pb2.SetImageFilterRequest(deviceID=deviceID, filters=filters))
    except grpc.RpcError as e:
      print(f'Cannot set the ImageLog Filter: {e}')
      raise

  def enableMonitoring(self, deviceID):
    try:
      self.stub.EnableMonitoring(event_pb2.EnableMonitoringRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot enable monitoring: {e}')
      raise

  def disableMonitoring(self, deviceID):
    try:
      self.stub.DisableMonitoring(event_pb2.DisableMonitoringRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.NOT_FOUND:
        print(f'Warning: disableMonitoring returned NOT_FOUND (maybe already disconnected).')
        return
      else:
        print(f'Cannot disable monitoring: {e}')
        raise

  def subscribe(self, queueSize): 
    try:
      return self.stub.SubscribeRealtimeLog(event_pb2.SubscribeRealtimeLogRequest(queueSize=queueSize))
    except grpc.RpcError as e:
      print(f'Cannot subscribe: {e}')
      raise

  def initCodeMap(self, filename):
    try:
      with open(filename) as f:
        self.codeMap = json.load(f)
    except:
      e = sys.exc_info()[0]
      print(f'Cannot init the event code map: {e}') 

  def getEventString(self, eventCode, subCode):
    if self.codeMap == None:
      return "No code map(%#X)" % (eventCode | subCode)
    else:
      for entry in self.codeMap['entries']:
        if eventCode == entry['event_code'] and subCode == entry['sub_code']:
          return entry['desc']

      # The problem is that the main+sub form cannot be found.  by charlie. 2024.07.22
      for entry in self.codeMap['entries']:
        if (eventCode | subCode) == entry['event_code']:
          return entry['desc']

      return "Unknown code(%#X)" % (eventCode | subCode)

  def getDeviceIOStates(self, deviceID, slaveIDs):
    try:
      response = self.stub.GetDeviceIOStates(event_pb2.GetDeviceIOStatesRequest(deviceID=deviceID, slaveIDs=slaveIDs))
      return response.states
    except grpc.RpcError as e:
      print(f'Cannot get the device IO states: {e}')
      raise
