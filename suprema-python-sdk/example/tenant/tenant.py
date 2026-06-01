import grpc

import tenant_pb2_grpc
import tenant_pb2


class TenantSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = tenant_pb2_grpc.TenantStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the tenant stub: {e}')
      raise

  def getList(self):
    try:
      response = self.stub.GetList(tenant_pb2.GetListRequest())
      return response.tenantIDs
    except grpc.RpcError as e:
      print(f'Cannot get the tenant list: {e}')
      raise

  def get(self, tenantIDs):
    try:
      response = self.stub.Get(tenant_pb2.GetRequest(tenantIDs=tenantIDs))
      return response.tenantInfos
    except grpc.RpcError as e:
      # print(f'Cannot get the tenant infos: {e}')
      raise

  def add(self, tenantInfos):
    try:
      self.stub.Add(tenant_pb2.AddRequest(tenantInfos=tenantInfos))
    except grpc.RpcError as e:
      print(f'Cannot add the tenant infos: {e}')
      raise

  def delete(self, tenantIDs):
    try:
      self.stub.Delete(tenant_pb2.DeleteRequest(tenantIDs=tenantIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the tenants: {e}')
      raise

  def addGateway(self, tenantID, gatewayIDs):
    try:
      self.stub.AddGateway(tenant_pb2.AddGatewayRequest(tenantID=tenantID, gatewayIDs=gatewayIDs))
    except grpc.RpcError as e:
      print(f'Cannot add the gateways: {e}')
      raise

  def deleteGateway(self, tenantID, gatewayIDs):
    try:
      self.stub.DeleteGateway(tenant_pb2.DeleteGatewayRequest(tenantID=tenantID, gatewayIDs=gatewayIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete the gateways: {e}')
      raise

  def getIssueranceHistory(self, tenantIDs):
    try:
      response = self.stub.GetIssuanceHistory(tenant_pb2.GetIssuanceHistoryRequest(tenantIDs=tenantIDs))
      return response.certInfos
    except grpc.RpcError as e:
      print(f'Cannot get the issuerance history: {e}')
      raise
