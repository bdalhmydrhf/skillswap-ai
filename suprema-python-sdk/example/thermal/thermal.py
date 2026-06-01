import grpc

import thermal_pb2_grpc
import thermal_pb2


class ThermalSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = thermal_pb2_grpc.ThermalStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the thermal stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(thermal_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the thermal config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(thermal_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the thermal config: {e}')
      raise

  def getTemperatureLog(self, deviceID, startEventID, maxNumOfLog):
    try:
      response = self.stub.GetTemperatureLog(thermal_pb2.GetTemperatureLogRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog))
      return response.temperatureEvents
    except grpc.RpcError as e:
      print(f'Cannot get the temperature event log: {e}')
      raise
