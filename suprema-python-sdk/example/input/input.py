import grpc

import input_pb2_grpc
import input_pb2


class InputSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = input_pb2_grpc.InputStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the input stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(input_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Input config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(input_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Input config: {e}')
      raise
