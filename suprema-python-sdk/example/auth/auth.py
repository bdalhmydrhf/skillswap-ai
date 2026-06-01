import grpc

import auth_pb2_grpc
import auth_pb2


class AuthSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = auth_pb2_grpc.AuthStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the auth stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(auth_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the auth config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(auth_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the auth config: {e}')
      raise
