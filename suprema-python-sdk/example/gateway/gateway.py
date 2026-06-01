import grpc

import gateway_pb2_grpc
import gateway_pb2


class GatewaySvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = gateway_pb2_grpc.GatewayStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the gateway stub: {e}')
      raise

  def getList(self):
    try:
      response = self.stub.GetList(gateway_pb2.GetListRequest())
      return response.gatewayIDs
    except grpc.RpcError as e:
      print(f'Cannot get the gateway list: {e}')
      raise

  def get(self, gatewayIDs):
    try:
      response = self.stub.Get(gateway_pb2.GetRequest(gatewayIDs=gatewayIDs))
      return response.gatewayInfos
    except grpc.RpcError as e:
      # print(f'Cannot get the gateway infos: {e}')
      raise

  def add(self, gatewayIDs):
    try:
      self.stub.Add(gateway_pb2.AddRequest(gatewayIDs=gatewayIDs))
    except grpc.RpcError as e:
      print(f'Cannot add the gateways: {e}')
      raise

  def delete(self, gatewayIDs):
    try:
      self.stub.Delete(gateway_pb2.DeleteRequest(gatewayIDs=gatewayIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the gateways: {e}')
      raise

  def getIssueranceHistory(self, gatewayIDs):
    try:
      response = self.stub.GetIssuanceHistory(gateway_pb2.GetIssuanceHistoryRequest(gatewayIDs=gatewayIDs))
      return response.certInfos
    except grpc.RpcError as e:
      print(f'Cannot get the issuerance history: {e}')
      raise
