import grpc

import wiegand_pb2_grpc
import wiegand_pb2


class WiegandSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = wiegand_pb2_grpc.WiegandStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the wiegand stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(wiegand_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the wiegand config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(wiegand_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the wiegand config: {e}')
      raise