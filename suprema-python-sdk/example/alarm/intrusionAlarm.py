import grpc

import intrusion_zone_pb2_grpc
import intrusion_zone_pb2


class IntrusionAlarmZoneSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = intrusion_zone_pb2_grpc.IntrusionAlarmZoneStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the intrusion_zone stub: {e}')
      raise

  def get(self, deviceID):
    try:
      response = self.stub.Get(intrusion_zone_pb2.GetRequest(deviceID=deviceID))
      return response.zones
    except grpc.RpcError as e:
      print(f'Cannot get the intrusionAlarm zones: {e}')
      raise

  def getStatus(self, deviceID, zoneIDs):
    try:
      response = self.stub.GetStatus(intrusion_zone_pb2.GetStatusRequest(deviceID=deviceID, zoneIDs=zoneIDs))
      return response.status
    except grpc.RpcError as e:
      print(f'Cannot get the zone status: {e}')
      raise

  def add(self, deviceID, zones):
    try:
      self.stub.Add(intrusion_zone_pb2.AddRequest(deviceID=deviceID, zones=zones))
    except grpc.RpcError as e:
      print(f'Cannot add the intrusionAlarm zones: {e}')
      raise

  def delete(self, deviceID, zoneIDs):
    try:
      self.stub.Delete(intrusion_zone_pb2.DeleteRequest(deviceID=deviceID, zoneIDs=zoneIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the intrusionAlarm zones: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(intrusion_zone_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the intrusionAlarm zones: {e}')
      raise

  def setArm(self, deviceID, zoneIDs, armed):
    try:
      self.stub.SetArm(intrusion_zone_pb2.SetArmRequest(deviceID=deviceID, zoneIDs=zoneIDs, armed=armed))
    except grpc.RpcError as e:
      print(f'Cannot (dis)arm on the intrusionAlarm zones: {e}')
      raise

  def setAlarm(self, deviceID, zoneIDs, alarmed):
    try:
      self.stub.SetAlarm(intrusion_zone_pb2.SetAlarmRequest(deviceID=deviceID, zoneIDs=zoneIDs, alarmed=alarmed))
    except grpc.RpcError as e:
      print(f'Cannot set alarm on the intrusionAlarm zones: {e}')
      raise
