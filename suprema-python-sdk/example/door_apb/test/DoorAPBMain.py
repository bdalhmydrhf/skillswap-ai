import grpc
import logging
import connect_pb2

from SlaveConnect import SlaveConnect
from DoorAPBTest import DoorAPBTest
from LogTest import LogTest

from example.client.client import GatewayClient
from example.master.master import MasterClient
from example.login.login import LoginSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.connect.connect import ConnectSvc
from example.rs485.rs485 import RS485Svc
from example.door.door import DoorSvc
from example.access.access import AccessSvc
from example.auth.auth import AuthSvc
from example.user.user import UserSvc
from example.card.card import CardSvc
from example.event.event import EventSvc

GATEWAY_CA_FILE = 'c:/cert/gateway/ca.crt'
GATEWAY_ADDR = '192.168.43.108'
GATEWAY_PORT = 4000

MASTER_CA_FILE = 'c:/cert/master/master_ca.crt'
MASTER_ADDR = '192.168.43.108'
MASTER_PORT = 4010

TENANT_CERT_FILE = 'c:/cert/master/tenant_tenant1.crt'
TENANT_KEY_FILE = 'c:/cert/master/tenant_tenant1_key.pem'
MASTER_MODE = False

GATEWAY_ID = 'gateway1'

DEVICE_ADDR = '192.168.40.26'
DEVICE_PORT = 51211
DEVICE_USE_SSL = False

CODE_MAP_FILE = '../../event/event_code.json'


def DoorAPBMain():
  client_ = None
  channel_ = None
  connectSvc_ = None
  rs485Svc_ = None
  doorSvc_ = None
  accessSvc_ = None
  authSvc_ = None
  userSvc_ = None
  cardSvc_ = None
  eventSvc_ = None
  deviceID = 0
  slaveID = 0

  try:
    if MASTER_MODE:
      client_ = MasterClient(MASTER_ADDR, MASTER_PORT, MASTER_CA_FILE, TENANT_CERT_FILE, TENANT_KEY_FILE)
      channel_ = client_.getChannel()

      loginSvc = LoginSvc(channel_)
      jwtToken = loginSvc.login(TENANT_CERT_FILE)

      client_.setToken(jwtToken)
      connectSvc_ = ConnectMasterSvc(channel_)
    else:
      client_ = GatewayClient(GATEWAY_ADDR, GATEWAY_PORT, GATEWAY_CA_FILE)
      channel_ = client_.getChannel()

      connectSvc_ = ConnectSvc(channel_)
  except grpc.RpcError as e:
    print(f'Cannot connect to the gateway: {e}', flush=True)
    raise

  connInfo = connect_pb2.ConnectInfo(IPAddr=DEVICE_ADDR, port=DEVICE_PORT, useSSL=DEVICE_USE_SSL)

  try:
    if MASTER_MODE:
      deviceID = connectSvc_.connect(GATEWAY_ID, connInfo)
    else:
      deviceID = connectSvc_.connect(connInfo)
  except grpc.RpcError as e:
    print(f'Cannot connect to the device: {e}', flush=True)
    raise

  rs485Svc_ = RS485Svc(channel_)
  doorSvc_ = DoorSvc(channel_)
  accessSvc_ = AccessSvc(channel_)
  authSvc_ = AuthSvc(channel_)
  userSvc_ = UserSvc(channel_)
  cardSvc_ = CardSvc(channel_)
  eventSvc_ = EventSvc(channel_)

  try:
    slaveID = SlaveConnect(rs485Svc_).getFirstSlave(deviceID)
    if 0 == slaveID:
      raise ValueError('No slaves')
  except grpc.RpcError as e:
    print(f'Cannot connect to the device: {deviceID}', flush=True)
    if MASTER_MODE:
      connectSvc_.disconnectAll(GATEWAY_ID)
    else:
      connectSvc_.disconnectAll()
    channel_.close()
    raise

  try:
    apbTest = DoorAPBTest(doorSvc_, accessSvc_, authSvc_, userSvc_, cardSvc_)
    if 0 < slaveID:
      logTest = LogTest(eventSvc_)
      logTest.startMonitoring(deviceID)

      apbTest.setDoor(deviceID, slaveID)
      apbTest.setAccessGroup(deviceID)
      apbTest.updateAuthConfig(deviceID)

      apbTest.enrollUser(deviceID)

      logTest.stopMonitoring(deviceID)
  except grpc.RpcError as e:
    print(f'Cannot complete the door test for device: {e}', flush=True)
  finally:
    if MASTER_MODE:
      connectSvc_.disconnectAll(GATEWAY_ID)
    else:
      connectSvc_.disconnectAll()

    channel_.close()

if __name__ == '__main__':
    logging.basicConfig()
    DoorAPBMain()
