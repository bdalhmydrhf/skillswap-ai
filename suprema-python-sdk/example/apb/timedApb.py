import grpc

import timed_apb_zone_pb2_grpc
import timed_apb_zone_pb2


class TimedAPBZoneSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = timed_apb_zone_pb2_grpc.TimedAPBZoneStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the timed_apb_zone stub: {e}')
      raise

  def get(self, deviceID):
    try:
      response = self.stub.Get(timed_apb_zone_pb2.GetRequest(deviceID=deviceID))
      return response.zones
    except grpc.RpcError as e:
      print(f'Cannot get the timed apb zones: {e}')
      raise

  def getStatus(self, deviceID, zoneIDs):
    try:
      response = self.stub.GetStatus(timed_apb_zone_pb2.GetStatusRequest(deviceID=deviceID, zoneIDs=zoneIDs))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the timed zone status: {e}')
      raise

  def add(self, deviceID, zones):
    try:
      self.stub.Add(timed_apb_zone_pb2.AddRequest(deviceID=deviceID, zones=zones))
    except grpc.RpcError as e:
      print(f'Cannot add the timed apb zones: {e}')
      raise

  def delete(self, deviceID, zoneIDs):
    try:
      self.stub.Delete(timed_apb_zone_pb2.DeleteRequest(deviceID=deviceID, zoneIDs=zoneIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the timed apb zones: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(timed_apb_zone_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the timed apb zones: {e}')
      raise

  def clear(self, deviceID, zoneID, userIDs):
    try:
      self.stub.Clear(timed_apb_zone_pb2.ClearRequest(deviceID=deviceID, zoneID=zoneID, userIDs=userIDs))
    except grpc.RpcError as e:
      print(f'Cannot clear the timed APB records: {e}')
      raise

  def clearAll(self, deviceID, zoneID):
    try:
      self.stub.ClearAll(timed_apb_zone_pb2.ClearAllRequest(deviceID=deviceID, zoneID=zoneID))
    except grpc.RpcError as e:
      print(f'Cannot clear all timed APB records: {e}')
      raise

  def setAlarm(self, deviceID, zoneIDs, alarmed):
    try:
      self.stub.SetAlarm(timed_apb_zone_pb2.SetAlarmRequest(deviceID=deviceID, zoneIDs=zoneIDs, alarmed=alarmed))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the timed apb zones: {e}')
      raise
    