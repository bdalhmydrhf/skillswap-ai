import grpc
import threading
import sys

import connect_pb2
import tenant_pb2

from example.master.master import MasterClient
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.login.login import LoginSvc
from example.tenant.tenant import TenantSvc
from example.connectMaster.test.cli.mainMenu import MainMenu

from example.cli.input import UserInput

DEVICE_IP = '192.168.0.110'
DEVICE_PORT = 51211
USE_SSL = False

MASTER_CA_FILE = "../../../../cert/master/ca.crt"
MASTER_IP = "192.168.0.2"
MASTER_PORT = 4010
ADMIN_CERT_FILE = "../../../../cert/master/admin.crt"
ADMIN_KEY_FILE = "../../../../cert/master/admin_key.pem"
TENANT_CERT_FILE = "../../../../cert/master/tenant1.crt"
TENANT_KEY_FILE = "../../../../cert/master/tenant1_key.pem"

TENANT_ID = "tenant1"
GATEWAY_ID = "gateway1"

QUEUE_SIZE = 16

def getDeviceStatus(statusCh):
  try:
    for status in statusCh:
      if status.status == connect_pb2.DISCONNECTED:
        print(f'[DISCONNECTED] Device {status.deviceID}', flush=True)
      elif status.status == connect_pb2.TLS_CONNECTED:
        print(f'[TLS_CONNECTED] Device {status.deviceID}', flush=True)
      elif status.status == connect_pb2.TCP_CONNECTED:
        print(f'[TCP_CONNECTED] Device {status.deviceID}', flush=True)
  
  except grpc.RpcError as e:
    if e.code() == grpc.StatusCode.CANCELLED:
      print('Subscription is cancelled', flush=True)    
    else:
      print(f'Cannot get the device status: {e}')   

def initMasterGateway():
  try:
    client = MasterClient(MASTER_IP, MASTER_PORT, MASTER_CA_FILE, ADMIN_CERT_FILE, ADMIN_KEY_FILE)
    channel = client.getChannel()

    loginSvc = LoginSvc(channel)
    jwtToken = loginSvc.loginAdmin(ADMIN_CERT_FILE)

    client.setToken(jwtToken)

    tenantSvc = TenantSvc(channel)

    try:
      tenantInfos = tenantSvc.get([TENANT_ID])
      print(f'{TENANT_ID} is already registered')
    except grpc.RpcError as e:
      print(f' {TENANT_ID} is not registered. Trying to add the tenant...', flush=True)
      tenantInfo = tenant_pb2.TenantInfo(tenantID=TENANT_ID, gatewayIDs=[GATEWAY_ID])
      tenantSvc.add([tenantInfo])
      print(f'{TENANT_ID} is registered successfully')
    
    channel.close()    
    return
  except grpc.RpcError as e:
    print(f'Cannot initialize the master gateway: {e}', flush=True)
    raise        

def testConnect():
  for arg in sys.argv:
    if arg == '-i':
      initMasterGateway()
      return

  client = MasterClient(MASTER_IP, MASTER_PORT, MASTER_CA_FILE, TENANT_CERT_FILE, TENANT_KEY_FILE)
  channel = client.getChannel()

  loginSvc = LoginSvc(channel)
  jwtToken = loginSvc.login(TENANT_CERT_FILE)

  client.setToken(jwtToken)

  connectMasterSvc = ConnectMasterSvc(channel)  

  statusCh = connectMasterSvc.subscribe(QUEUE_SIZE)
  statusThread = threading.Thread(target=getDeviceStatus, args=(statusCh,))
  statusThread.start()

  mainMenu = MainMenu(connectMasterSvc, GATEWAY_ID)
  mainMenu.show()

  statusCh.cancel()
  statusThread.join()

if __name__ == '__main__':
    testConnect()