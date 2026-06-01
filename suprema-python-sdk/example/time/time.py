import grpc

import time_pb2_grpc
import time_pb2


class TimeSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = time_pb2_grpc.TimeStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the time stub: {e}')
      raise

  def getTime(self, deviceID):
    try:
      response = self.stub.Get(time_pb2.GetRequest(deviceID=deviceID))
      return response.GMTTime
    except grpc.RpcError as e:
      print(f'Cannot get time: {e}')
      raise

  def setTime(self, deviceID, GMTTime):
    try:
      self.stub.Set(time_pb2.SetRequest(deviceID=deviceID, GMTTime=GMTTime))
    except grpc.RpcError as e:
      print(f'Cannot set time: {e}')
      raise

  def getDSTConfig(self, deviceID):
    try:
      response = self.stub.GetDSTConfig(time_pb2.GetDSTConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the DST config: {e}')
      raise

  def setDSTConfig(self, deviceID, config):
    try:
      self.stub.SetDSTConfig(time_pb2.SetDSTConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the DST config: {e}')
      raise
