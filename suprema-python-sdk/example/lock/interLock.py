import grpc

import interlock_zone_pb2_grpc
import interlock_zone_pb2


class InterlockZoneSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = interlock_zone_pb2_grpc.InterlockZoneStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the interlock_zone stub: {e}')
      raise

  def get(self, deviceID):
    try:
      response = self.stub.Get(interlock_zone_pb2.GetRequest(deviceID=deviceID))
      return response.zones
    except grpc.RpcError as e:
      print(f'Cannot get the interLock zones: {e}')
      raise

  def getStatus(self, deviceID, zoneIDs):
    try:
      response = self.stub.GetStatus(interlock_zone_pb2.GetStatusRequest(deviceID=deviceID, zoneIDs=zoneIDs))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the zone status: {e}')
      raise

  def add(self, deviceID, zones):
    try:
      self.stub.Add(interlock_zone_pb2.AddRequest(deviceID=deviceID, zones=zones))
    except grpc.RpcError as e:
      print(f'Cannot add the interLock zones: {e}')
      raise

  def delete(self, deviceID, zoneIDs):
    try:
      self.stub.Delete(interlock_zone_pb2.DeleteRequest(deviceID=deviceID, zoneIDs=zoneIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the interLock zones: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(interlock_zone_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the interLock zones: {e}')
      raise

  def setAlarm(self, deviceID, zoneIDs, alarmed):
    try:
      self.stub.SetAlarm(interlock_zone_pb2.SetAlarmRequest(deviceID=deviceID, zoneIDs=zoneIDs, alarmed=alarmed))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the interLock zones: {e}')
      raise
