import grpc

import voip_pb2_grpc
import voip_pb2


class VoipSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = voip_pb2_grpc.VOIPStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the voip stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(voip_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the voip config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(voip_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the voip config: {e}')
      raise
