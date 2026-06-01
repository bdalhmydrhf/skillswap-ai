import grpc
import logging

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.card.card import CardSvc
from example.user.user import UserSvc
from example.event.event import EventSvc

from example.cli.input import UserInput

from config import TestConfig
from menu import TestMenu
from device import DeviceMgr
from event import EventMgr
from user import UserMgr

GATEWAY_CA_FILE = '../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.43.108'
GATEWAY_PORT = 4000

SYNC_CONFIG_FILE = "./example/sync/sync_config.json"
CODE_MAP_FILE = "./example/event/event_code.json"

def testSync():
  try:
    client = GatewayClient(GATEWAY_IP, GATEWAY_PORT, GATEWAY_CA_FILE)
    channel = client.getChannel()
    
    connectSvc = ConnectSvc(channel)
    cardSvc = CardSvc(channel)
    userSvc = UserSvc(channel)
    eventSvc = EventSvc(channel)
    eventSvc.initCodeMap(CODE_MAP_FILE)    
    
    testConfig = TestConfig(SYNC_CONFIG_FILE)

    deviceMgr = DeviceMgr(connectSvc, testConfig)
    eventMgr = EventMgr(eventSvc, testConfig)
    userMgr = UserMgr(userSvc, cardSvc, testConfig, deviceMgr, eventMgr)

    print('Trying to connect to the devices...', flush=True)

    deviceMgr.handleConnection(eventMgr.handleConnection)
    deviceMgr.connectToDevices()
    eventMgr.handleEvent(userMgr.syncUser)

    UserInput.pressEnter('\n>>> Press ENTER to show the test menu\n')
    TestMenu(userMgr, deviceMgr, eventMgr, testConfig).show()

    deviceMgr.deleteConnection()
    channel.close()    

  except grpc.RpcError as e:
    print(f'Cannot run the sync test example: {e}')


if __name__ == '__main__':
    logging.basicConfig()
    testSync()
