import grpc

import rs485_pb2_grpc
import rs485_pb2


class RS485Svc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = rs485_pb2_grpc.RS485Stub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the rs485 stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(rs485_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the rs485 config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(rs485_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the rs485 config: {e}')
      raise

  def searchSlave(self, deviceID):
    try:
      response = self.stub.SearchDevice(rs485_pb2.SearchDeviceRequest(deviceID=deviceID))
      return response.slaveInfos
    except grpc.RpcError as e:
      print(f'Cannot search slave devices: {e}')
      raise

  def getSlave(self, deviceID):
    try:
      response = self.stub.GetDevice(rs485_pb2.GetDeviceRequest(deviceID=deviceID))
      return response.slaveInfos
    except grpc.RpcError as e:
      print(f'Cannot get slave devices: {e}')
      raise    

  def setSlave(self, deviceID, slaveInfos):
    try:
      self.stub.SetDevice(rs485_pb2.SetDeviceRequest(deviceID=deviceID, slaveInfos=slaveInfos))
    except grpc.RpcError as e:
      print(f'Cannot set slave devices: {e}')
      raise        