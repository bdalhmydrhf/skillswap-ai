import grpc

import system_pb2_grpc
import system_pb2


class SystemSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = system_pb2_grpc.SystemStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the system stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(system_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the System config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(system_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the System config: {e}')
      raise
