import grpc

import lift_pb2_grpc
import lift_pb2


class LiftSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = lift_pb2_grpc.LiftStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the lift stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(lift_pb2.GetListRequest(deviceID=deviceID))
      return response.lifts
    except grpc.RpcError as e:
      print(f'Cannot get the lift list: {e}')
      raise

  def getStatus(self, deviceID):
    try:
      response = self.stub.GetStatus(lift_pb2.GetStatusRequest(deviceID=deviceID))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the lift status: {e}')
      raise

  def add(self, deviceID, lifts):
    try:
      self.stub.Add(lift_pb2.AddRequest(deviceID=deviceID, lifts=lifts))
    except grpc.RpcError as e:
      print(f'Cannot add lifts: {e}')
      raise

  def delete(self, deviceID, liftIDs):
    try:
      self.stub.Delete(lift_pb2.DeleteRequest(deviceID=deviceID, liftIDs=liftIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the lifts: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(lift_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the lifts: {e}')
      raise

  def activate(self, deviceID, liftID, floorIndices, flag):
    try:
      self.stub.Activate(lift_pb2.ActivateRequest(deviceID=deviceID, liftID=liftID, floorIndexes=floorIndices, activateFlag=flag))
    except grpc.RpcError as e:
      print(f'Cannot activate the lift: {e}')
      raise

  def deactivate(self, deviceID, liftID, floorIndices, flag):
    try:
      self.stub.Deactivate(lift_pb2.DeactivateRequest(deviceID=deviceID, liftID=liftID, floorIndexes=floorIndices, deactivateFlag=flag))
    except grpc.RpcError as e:
      print(f'Cannot deactivate the lift: {e}')
      raise

  def release(self, deviceID, liftID, floorIndices, flag):
    try:
      self.stub.Release(lift_pb2.ReleaseRequest(deviceID=deviceID, liftID=liftID, floorIndexes=floorIndices, floorFlag=flag))
    except grpc.RpcError as e:
      print(f'Cannot release the lift flags: {e}')
      raise

  def setAlarm(self, deviceID, liftIDs, flag):
    try:
      self.stub.SetAlarm(lift_pb2.SetAlarmRequest(deviceID=deviceID, liftIDs=liftIDs, alarmFlag=flag))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the lifts: {e}')
      raise
    