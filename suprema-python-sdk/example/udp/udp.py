import grpc

import udp_pb2_grpc
import udp_pb2


class UdpSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = udp_pb2_grpc.UDPStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the udp stub: {e}')
      raise

  def getIPConfig(self, deviceInfo):
    try:
      response = self.stub.GetIPConfig(udp_pb2.GetIPConfigRequest(deviceInfo=deviceInfo))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the IP config: {e}')
      raise

  def setIPConfig(self, deviceInfo, config):
    try:
      self.stub.SetIPConfig(udp_pb2.SetIPConfigRequest(deviceInfo=deviceInfo, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the IP config: {e}')
      raise
