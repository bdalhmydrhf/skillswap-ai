import grpc

import apb_zone_pb2_grpc
import apb_zone_pb2


class APBZoneSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = apb_zone_pb2_grpc.APBZoneStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the apb_zone stub: {e}')
      raise

  def get(self, deviceID):
    try:
      response = self.stub.Get(apb_zone_pb2.GetRequest(deviceID=deviceID))
      return response.zones
    except grpc.RpcError as e:
      print(f'Cannot get the apb zones: {e}')
      raise

  def getStatus(self, deviceID, zoneIDs):
    try:
      response = self.stub.GetStatus(apb_zone_pb2.GetStatusRequest(deviceID=deviceID, zoneIDs=zoneIDs))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the zone status: {e}')
      raise

  def add(self, deviceID, zones):
    try:
      self.stub.Add(apb_zone_pb2.AddRequest(deviceID=deviceID, zones=zones))
    except grpc.RpcError as e:
      print(f'Cannot add the apb zones: {e}')
      raise

  def delete(self, deviceID, zoneIDs):
    try:
      self.stub.Delete(apb_zone_pb2.DeleteRequest(deviceID=deviceID, zoneIDs=zoneIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the apb zones: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(apb_zone_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the apb zones: {e}')
      raise

  def clear(self, deviceID, zoneID, userIDs):
    try:
      self.stub.Clear(apb_zone_pb2.ClearRequest(deviceID=deviceID, zoneID=zoneID, userIDs=userIDs))
    except grpc.RpcError as e:
      print(f'Cannot clear the APB records: {e}')
      raise

  def clearAll(self, deviceID, zoneID):
    try:
      self.stub.ClearAll(apb_zone_pb2.ClearAllRequest(deviceID=deviceID, zoneID=zoneID))
    except grpc.RpcError as e:
      print(f'Cannot clear all APB records: {e}')
      raise

  def setAlarm(self, deviceID, zoneIDs, alarmed):
    try:
      self.stub.SetAlarm(apb_zone_pb2.SetAlarmRequest(deviceID=deviceID, zoneIDs=zoneIDs, alarmed=alarmed))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the apb zones: {e}')
      raise
