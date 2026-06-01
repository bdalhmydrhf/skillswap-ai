import grpc

import udp_master_pb2_grpc
import udp_master_pb2


class UdpMasterSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = udp_master_pb2_grpc.UDPMasterStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the udp stub: {e}')
      raise

  def getIPConfig(self, gatewayID, deviceInfo):
    try:
      response = self.stub.GetIPConfig(udp_master_pb2.GetIPConfigRequest(gatewayID=gatewayID, deviceInfo=deviceInfo))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the IP config: {e}')
      raise

  def setIPConfig(self, gatewayID, deviceInfo, config):
    try:
      self.stub.SetIPConfig(udp_master_pb2.SetIPConfigRequest(gatewayID=gatewayID, deviceInfo=deviceInfo, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the IP config: {e}')
      raise
