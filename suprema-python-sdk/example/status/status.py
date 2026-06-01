import grpc

import status_pb2_grpc
import status_pb2


class StatusSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = status_pb2_grpc.StatusStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the status stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(status_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the status config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(status_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the status config: {e}')
      raise