import grpc

import network_pb2_grpc
import network_pb2


class NetworkSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = network_pb2_grpc.NetworkStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the network stub: {e}')
      raise

  def getIPConfig(self, deviceID):
    try:
      response = self.stub.GetIPConfig(network_pb2.GetIPConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the IP config: {e}')
      raise

  def setIPConfig(self, deviceID, config):
    try:
      self.stub.SetIPConfig(network_pb2.SetIPConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the IP config: {e}')
      raise

  def getWLANConfig(self, deviceID):
    try:
      response = self.stub.GetWLANConfig(network_pb2.GetWLANConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the WLAN config: {e}')
      raise

  def setWLANConfig(self, deviceID, config):
    try:
      self.stub.SetWLANConfig(network_pb2.SetWLANConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the WLAN config: {e}')
      raise
