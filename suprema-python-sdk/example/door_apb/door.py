import grpc

import door_pb2_grpc
import door_pb2


class DoorSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = door_pb2_grpc.DoorStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the door stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(door_pb2.GetListRequest(deviceID=deviceID))
      return response.doors
    except grpc.RpcError as e:
      print(f'Cannot get the door list: {e}')
      raise

  def getStatus(self, deviceID):
    try:
      response = self.stub.GetStatus(door_pb2.GetStatusRequest(deviceID=deviceID))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the door status: {e}')
      raise

  def add(self, deviceID, doors):
    try:
      self.stub.Add(door_pb2.AddRequest(deviceID=deviceID, doors=doors))
    except grpc.RpcError as e:
      print(f'Cannot add doors: {e}')
      raise

  def delete(self, deviceID, doorIDs):
    try:
      self.stub.Delete(door_pb2.DeleteRequest(deviceID=deviceID, doorIDs=doorIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the doors: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(door_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the doors: {e}')
      raise

  def lock(self, deviceID, doorIDs, doorFlag):
    try:
      self.stub.Lock(door_pb2.LockRequest(deviceID=deviceID, doorIDs=doorIDs, doorFlag=doorFlag))
    except grpc.RpcError as e:
      print(f'Cannot lock the doors: {e}')
      raise

  def unlock(self, deviceID, doorIDs, doorFlag):
    try:
      self.stub.Unlock(door_pb2.UnlockRequest(deviceID=deviceID, doorIDs=doorIDs, doorFlag=doorFlag))
    except grpc.RpcError as e:
      print(f'Cannot unlock the doors: {e}')
      raise

  def release(self, deviceID, doorIDs, doorFlag):
    try:
      self.stub.Release(door_pb2.ReleaseRequest(deviceID=deviceID, doorIDs=doorIDs, doorFlag=doorFlag))
    except grpc.RpcError as e:
      print(f'Cannot release the door flags: {e}')
      raise

  def setAlarm(self, deviceID, doorIDs, flag):
    try:
      self.stub.SetAlarm(door_pb2.SetAlarmRequest(deviceID=deviceID, doorIDs=doorIDs, alarmFlag=flag))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the doors: {e}')
      raise
