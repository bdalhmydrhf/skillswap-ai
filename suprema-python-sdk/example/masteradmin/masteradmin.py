import grpc

import masteradmin_pb2_grpc
import masteradmin_pb2


class MasterAdminSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = masteradmin_pb2_grpc.MasterAdminStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the master admin stub: {e}')
      raise

  def get(self, deviceID):
    try:
      response = self.stub.Get(masteradmin_pb2.GetRequest(deviceID=deviceID))
      return response.masterAdmin
    except grpc.RpcError as e:
      print(f'Cannot get the master admin: {e}')
      raise

  def set(self, deviceID, masteradmin):
    try:
      self.stub.Set(masteradmin_pb2.SetRequest(deviceID=deviceID, masterAdmin=masteradmin))
    except grpc.RpcError as e:
      print(f'Cannot set the master admin: {e}')
      raise

  def setMulti(self, deviceIDs, masteradmin):
    try:
      self.stub.SetMulti(masteradmin_pb2.SetMultiRequest(deviceIDs=deviceIDs, masterAdmin=masteradmin))
    except grpc.RpcError as e:
      print(f'Cannot set the master admin multi: {e}')
      raise
