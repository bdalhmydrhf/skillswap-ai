import grpc

import access_pb2_grpc
import access_pb2


class AccessSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = access_pb2_grpc.AccessStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the access stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(access_pb2.GetListRequest(deviceID=deviceID))
      return response.groups
    except grpc.RpcError as e:
      print(f'Cannot get the access groups: {e}')
      raise

  def add(self, deviceID, groups):
    try:
      self.stub.Add(access_pb2.AddRequest(deviceID=deviceID, groups=groups))
    except grpc.RpcError as e:
      print(f'Cannot add access groups: {e}')
      raise

  def delete(self, deviceID, groupIDs):
    try:
      self.stub.Delete(access_pb2.DeleteRequest(deviceID=deviceID, groupIDs=groupIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete access groups: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(access_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the access groups: {e}')
      raise

  def getLevelList(self, deviceID):
    try:
      response = self.stub.GetLevelList(access_pb2.GetLevelListRequest(deviceID=deviceID))
      return response.levels
    except grpc.RpcError as e:
      print(f'Cannot get the access levels: {e}')
      raise

  def addLevel(self, deviceID, levels):
    try:
      self.stub.AddLevel(access_pb2.AddLevelRequest(deviceID=deviceID, levels=levels))
    except grpc.RpcError as e:
      print(f'Cannot add access levels: {e}')
      raise

  def deleteLevel(self, deviceID, levelIDs):
    try:
      self.stub.DeleteLevel(access_pb2.DeleteLevelRequest(deviceID=deviceID, levelIDs=levelIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete access levels: {e}')
      raise

  def deleteAllLevel(self, deviceID):
    try:
      self.stub.DeleteAllLevel(access_pb2.DeleteAllLevelRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the access levels: {e}')
      raise

  def getFloorLevelList(self, deviceID):
    try:
      response = self.stub.GetFloorLevelList(access_pb2.GetFloorLevelListRequest(deviceID=deviceID))
      return response.levels
    except grpc.RpcError as e:
      print(f'Cannot get the floor levels: {e}')
      raise

  def addFloorLevel(self, deviceID, levels):
    try:
      self.stub.AddFloorLevel(access_pb2.AddFloorLevelRequest(deviceID=deviceID, levels=levels))
    except grpc.RpcError as e:
      print(f'Cannot add floor levels: {e}')
      raise

  def deleteFloorLevel(self, deviceID, levelIDs):
    try:
      self.stub.DeleteFloorLevel(access_pb2.DeleteFloorLevelRequest(deviceID=deviceID, levelIDs=levelIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete floor levels: {e}')
      raise

  def deleteAllFloorLevel(self, deviceID):
    try:
      self.stub.DeleteAllFloorLevel(access_pb2.DeleteAllFloorLevelRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the floor levels: {e}')
      raise
