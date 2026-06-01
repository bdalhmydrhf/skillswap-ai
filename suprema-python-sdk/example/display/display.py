import grpc

import display_pb2_grpc
import display_pb2


class DisplaySvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = display_pb2_grpc.DisplayStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the display stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(display_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Display config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(display_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Display config: {e}')
      raise
