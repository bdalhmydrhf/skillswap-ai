import grpc

import device_pb2_grpc
import device_pb2

from deprecated import deprecated

class DeviceSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = device_pb2_grpc.DeviceStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the device stub: {e}')
      raise

  def getInfo(self, deviceID):
    try:
      response = self.stub.GetInfo(device_pb2.GetInfoRequest(deviceID=deviceID))
      return response.info
    except grpc.RpcError as e:
      print(f'Cannot get the device info: {e}')
      raise

  def getHashKey(self, deviceID):
    try:
      response = self.stub.GetHashKey(device_pb2.GetHashKeyRequest(deviceID=deviceID))
      return (response.isDefault, response.checksum)
    except grpc.RpcError as e:
      print(f'Cannot get the device hashKey: {e}')
      raise

  def setHashKey(self, deviceID, setDefault, hashKey):
    try:
      self.stub.SetHashKey(device_pb2.SetHashKeyRequest(deviceID=deviceID, setDefault=setDefault, hashKey=hashKey))
    except grpc.RpcError as e:
      print(f'Cannot set the device hashKey: {e}')
      raise

  def getCapability(self, deviceID):
    try:
      response = self.stub.GetCapability(device_pb2.GetCapabilityRequest(deviceID=deviceID))
      return response.deviceCapability
    except grpc.RpcError as e:
      print(f'Cannot get the device capability: {e}')
      raise

  def getCapInfo(self, deviceID):
    try:
      response = self.stub.GetCapabilityInfo(device_pb2.GetCapabilityInfoRequest(deviceID=deviceID))
      return response.capInfo
    except grpc.RpcError as e:
      print(f'Cannot get the capability info: {e}')
      raise

  def lockDevice(self, deviceID):
    try:
      self.stub.Lock(device_pb2.LockRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot lock the device: {e}')
      raise

  def unlockDevice(self, deviceID):
    try:
      self.stub.Unlock(device_pb2.UnlockRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot unlock the device: {e}')
      raise

  def rebootDevice(self, deviceID):
    try:
      self.stub.Reboot(device_pb2.RebootRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot reboot the device: {e}')
      raise

  def resetDevice(self, deviceID):
    try:
      self.stub.FactoryReset(device_pb2.FactoryResetRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot reset the device: {e}')
      raise

  def resetConfig(self, deviceID, withNetwork=False, withDB=False):
    try:
      self.stub.ResetConfig(device_pb2.ResetConfigRequest(deviceID=deviceID, withNetwork=withNetwork, withDB=withDB))
    except grpc.RpcError as e:
      print(f'Cannot reset the config: {e}')
      raise

  def clearDatabase(self, deviceID):
    try:
      self.stub.ClearDB(device_pb2.ClearDBRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot clear the database: {e}')
      raise

  def upgradeFirmware(self, deviceID, firmwareData):
    try:
      self.stub.UpgradeFirmware(device_pb2.UpgradeFirmwareRequest(deviceID=deviceID, firmwareData=firmwareData))
    except grpc.RpcError as e:
      print(f'Cannot upgrade firmware: {e}')
      raise
