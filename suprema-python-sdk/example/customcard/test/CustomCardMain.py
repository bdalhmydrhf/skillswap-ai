import grpc
import logging
import connect_pb2

from CustomCardTest import CustomCardTest
from example.cli.input import UserInput

from example.client.client import GatewayClient
from example.master.master import MasterClient
from example.login.login import LoginSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.connect.connect import ConnectSvc
from example.device.device import DeviceSvc
from example.card.card import CardSvc
from example.system.system import SystemSvc


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

DEVICE_ADDR = '192.168.40.198'
DEVICE_PORT = 51211
DEVICE_USE_SSL = False



def CustomCardMain():
  client_ = None
  channel_ = None
  connectSvc_ = None
  deviceSvc_ = None
  cardSvc_ = None
  systemSvc_ = None
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
  cardSvc_ = CardSvc(channel_)
  systemSvc_ = SystemSvc(channel_)

  try:
    capability = deviceSvc_.getCapability(deviceID)
    print(f'Device capabilities=====:\n{capability}\n')
    if capability.customSmartCardSupported:
      cardTest = CustomCardTest(cardSvc_, systemSvc_)

      msg = """Please select a number
0: Exit
1: Get custom card config
2: Set custom card config
3: Scan card
=> """

      while True:
        inputValue = UserInput.getInteger(msg, 1, 0, 3)

        if inputValue == 1:
          cardTest.getCustomCardConfig(deviceID)
        elif inputValue == 2:
          cardTest.setCustomCardConfig(deviceID)
        elif inputValue == 3:
          cardTest.scanCard(deviceID)
        else:
          break

  except grpc.RpcError as e:
    print(f'Cannot complete the custom card config test for device: {e}', flush=True)
  finally:
    if MASTER_MODE:
      connectSvc_.disconnectAll(GATEWAY_ID)
    else:
      connectSvc_.disconnectAll()

    channel_.close()

if __name__ == '__main__':
    logging.basicConfig()
    CustomCardMain()
