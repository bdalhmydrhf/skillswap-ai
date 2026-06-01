import grpc
import logging
import connect_pb2

from FaceUserTest import FaceUserTest
from FaceEnrollMenu import MainMenuResourceType, showMenuMain

from example.client.client import GatewayClient
from example.master.master import MasterClient
from example.login.login import LoginSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.connect.connect import ConnectSvc
from example.device.device import DeviceSvc
from example.user.user import UserSvc
from example.face.face import FaceSvc

GATEWAY_CA_FILE = 'c:/cert/gateway/ca.crt'
GATEWAY_ADDR = '192.168.43.108'
GATEWAY_PORT = 4000

MASTER_CA_FILE = 'c:/cert/master/master_ca.crt'
MASTER_ADDR = '192.168.43.108'
MASTER_PORT = 4010

TENANT_CERT_FILE = 'c:/cert/master/tenant_tenant1.crt'
TENANT_KEY_FILE = 'c:/cert/master/tenant_tenant1_key.pem'
MASTER_MODE = True

GATEWAY_ID = 'gateway1'

DEVICE_ADDR = '192.168.40.3'
DEVICE_PORT = 51211
DEVICE_USE_SSL = False


def FaceEnrollMain():
  client_ = None
  channel_ = None
  connectSvc_ = None
  deviceSvc_ = None
  userSvc_ = None
  faceSvc_ = None
  deviceID = 0

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

  deviceSvc_ = DeviceSvc(channel_)
  userSvc_ = UserSvc(channel_)
  faceSvc_ = FaceSvc(channel_)

  try:
    capability = deviceSvc_.getCapability(deviceID)
    print(f'Device capabilities=====:\n{capability}\n')
    if capability.faceInputSupported and capability.faceExSupported:
      enrollTest = FaceUserTest(userSvc_, faceSvc_)

      while True:
        selectedItem = showMenuMain()
        if MainMenuResourceType.EXIT.value == selectedItem:
          break
        elif MainMenuResourceType.UPDATE_FACECONFIG_TEMPLATEONLY.value == selectedItem:
          enrollTest.updateFaceConfig(deviceID)
        elif MainMenuResourceType.GET_USER.value == selectedItem:
          enrollTest.getUsers(deviceID)
        elif MainMenuResourceType.REMOVE_USER.value == selectedItem:
          enrollTest.removeUsers(deviceID)
        elif MainMenuResourceType.ENROLL_USER.value == selectedItem:
          enrollTest.enrollUser(deviceID)
  except grpc.RpcError as e:
    print(f'Cannot complete the user test for device: {e}', flush=True)
  finally:
    if MASTER_MODE:
      connectSvc_.disconnectAll(GATEWAY_ID)
    else:
      connectSvc_.disconnectAll()

    channel_.close()

if __name__ == '__main__':
    logging.basicConfig()
    FaceEnrollMain()
