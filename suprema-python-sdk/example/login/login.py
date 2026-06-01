import grpc

import login_pb2_grpc
import login_pb2

ADMIN_TENANT_ID = "administrator"

class LoginSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = login_pb2_grpc.LoginStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the login stub: {e}')
      raise

  def login(self, tenantCertFile):
    try:
      with open(tenantCertFile, 'rb') as cert:
        response = self.stub.Login(login_pb2.LoginRequest(tenantCert=cert.read()))
        return response.jwtToken
    except grpc.RpcError as e:
      print(f'Cannot login: {e}')
      raise

  def loginAdmin(self, adminCertFile):
    try:
      with open(adminCertFile, 'rb') as cert:
        response = self.stub.LoginAdmin(login_pb2.LoginAdminRequest(adminTenantCert=cert.read(), tenantID=ADMIN_TENANT_ID))
        return response.jwtToken
    except grpc.RpcError as e:
      print(f'Cannot login as an administrator: {e}')
      raise

