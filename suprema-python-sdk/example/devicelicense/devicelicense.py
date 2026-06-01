import grpc

import devicelicense_pb2_grpc
import devicelicense_pb2


class DeviceLicenseSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = devicelicense_pb2_grpc.DeviceLicenseStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the device license stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(devicelicense_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the device license config: {e}')
      raise

  def enable(self, deviceID, licenseBlob):
    try:
      response = self.stub.Enable(devicelicense_pb2.EnableRequest(deviceID=deviceID, licenseBlob=licenseBlob))
      return response.results
    except grpc.RpcError as e:
      print(f'Cannot enable the device license: {e}')
      raise

  def disable(self, deviceID, licenseBlob):
    try:
      response = self.stub.Disable(devicelicense_pb2.DisableRequest(deviceID=deviceID, licenseBlob=licenseBlob))
      return response.results
    except grpc.RpcError as e:
      print(f'Cannot disable the device license: {e}')
      raise

  def query(self, deviceID, type):
    try:
      response = self.stub.Query(devicelicense_pb2.QueryRequest(deviceID=deviceID, type=type))
      return response.results
    except grpc.RpcError as e:
      print(f'Cannot query the device license: {e}')
      raise
