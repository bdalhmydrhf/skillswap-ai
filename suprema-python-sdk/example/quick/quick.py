import grpc
import logging
import sys

import tenant_pb2
import os

from testConnect import testConnect
from testConnect import testConnectMaster
from testDevice import testDevice
from testDisplay import testDisplay
from testFinger import testFinger
from testFace import testFace
from testCard import testCard
from testUser import testUser
from testEvent import testEvent

from example.client.client import GatewayClient
from example.master.master import MasterClient
from example.connect.connect import ConnectSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.login.login import LoginSvc
from example.device.device import DeviceSvc
from example.display.display import DisplaySvc
from example.finger.finger import FingerSvc
from example.face.face import FaceSvc
from example.card.card import CardSvc
from example.user.user import UserSvc
from example.event.event import EventSvc
from example.tenant.tenant import TenantSvc

GATEWAY_CA_FILE = '../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.43.108'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.40.62'
DEVICE_PORT = 51211
USE_SSL = False

MASTER_CA_FILE = "../../../cert/master/master_ca.crt"
MASTER_IP = "192.168.28.21"
MASTER_PORT = 4010
ADMIN_CERT_FILE = "../../../cert/master/admin.crt"
ADMIN_KEY_FILE = "../../../cert/master/admin_key.pem"
TENANT_CERT_FILE = "../../../cert/master/tenant2.crt"
TENANT_KEY_FILE = "../../../cert/master/tenant2_key.pem"

TENANT_ID = "tenant2"
GATEWAY_ID = "gateway2"

def testGateway():
  try:
    client = GatewayClient(GATEWAY_IP, GATEWAY_PORT, GATEWAY_CA_FILE)
    channel = client.getChannel()
    
    connectSvc = ConnectSvc(channel)
    devID = testConnect(connectSvc, DEVICE_IP, DEVICE_PORT, USE_SSL)

    testService(channel, devID)

    deviceIDs = [devID]
    connectSvc.disconnect(deviceIDs)

    devList = connectSvc.getDeviceList()
    print(f'\nDevice list: {devList}')

    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot test the device gateway: {e}', flush=True)
    raise   


def testService(channel, devID):
  try:
    deviceSvc = DeviceSvc(channel)
    displaySvc = DisplaySvc(channel)
    fingerSvc = FingerSvc(channel)
    faceSvc = FaceSvc(channel)
    cardSvc = CardSvc(channel)
    userSvc = UserSvc(channel)
    eventSvc = EventSvc(channel)

    capabilityInfo = testDevice(deviceSvc, devID)

    if capabilityInfo.faceSupported:
      testFace(faceSvc, devID)

    if capabilityInfo.fingerSupported:
      testFinger(fingerSvc, devID)

    if capabilityInfo.cardSupported:
      testCard(cardSvc, devID, capabilityInfo)
      
    testUser(userSvc, fingerSvc, faceSvc, devID, capabilityInfo)
    testEvent(eventSvc, devID)

  except grpc.RpcError as e:
    print(f'Cannot test the services: {e}', flush=True)
    raise   


def testMasterGateway():
  try:
    client = MasterClient(MASTER_IP, MASTER_PORT, MASTER_CA_FILE, TENANT_CERT_FILE, TENANT_KEY_FILE)
    channel = client.getChannel()

    loginSvc = LoginSvc(channel)
    jwtToken = loginSvc.login(TENANT_CERT_FILE)

    client.setToken(jwtToken)

    connectMasterSvc = ConnectMasterSvc(channel)
    devID = testConnectMaster(connectMasterSvc, GATEWAY_ID, DEVICE_IP, DEVICE_PORT, USE_SSL)

    testService(channel, devID)

    deviceIDs = [devID]
    connectMasterSvc.disconnect(deviceIDs)

    devList = connectMasterSvc.getDeviceList(GATEWAY_ID)
    print(f'\nDevice list: {devList}')    
    
    channel.close()    
    return
  except grpc.RpcError as e:
    print(f'Cannot test the master gateway: {e}', flush=True)
    raise   


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


def quickStart():
  masterMode = False

  for arg in sys.argv:
    if arg == '-mi':
      initMasterGateway()
      return
    elif arg == '-m':
      masterMode = True
    elif arg == '-g':
      os.environ['GRPC_VERBOSITY'] = 'debug'
      os.environ['GRPC_TRACE'] = 'api'

  try:
    if masterMode:
      testMasterGateway()
    else:
      testGateway()
  except grpc.RpcError as e:
    print(f'Cannot run the quick start example: {e}')


if __name__ == '__main__':
    logging.basicConfig()
    quickStart()
