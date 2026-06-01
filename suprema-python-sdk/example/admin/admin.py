import grpc

import admin_pb2_grpc
import admin_pb2


class AdminSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = admin_pb2_grpc.AdminStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the admin stub: {e}')
      raise

  def getInfo(self): 
    try:
      response = self.stub.GetInfo(admin_pb2.GetInfoRequest())
      return response.version, response.buildDate
    except grpc.RpcError as e:
      print(f'Cannot get info: {e}')
      raise
