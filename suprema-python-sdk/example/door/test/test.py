import grpc
import logging
import connect_pb2

from testEvent import TestEvent
from testDoor import TestDoor

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.event.event import EventSvc
from example.door.door import DoorSvc
from example.access.access import AccessSvc
from example.user.user import UserSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.0.2'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.0.110'
DEVICE_PORT = 51211
USE_SSL = False

CODE_MAP_FILE = '../../event/event_code.json'

def test():
  channel = None
  connectSvc = None
  devID = 0

  try:
    client = GatewayClient(GATEWAY_IP, GATEWAY_PORT, GATEWAY_CA_FILE)
    channel = client.getChannel()
    
    connectSvc = ConnectSvc(channel)
    connInfo = connect_pb2.ConnectInfo(IPAddr=DEVICE_IP, port=DEVICE_PORT, useSSL=USE_SSL)

    devID = connectSvc.connect(connInfo)

    eventSvc = EventSvc(channel)
    eventSvc.initCodeMap(CODE_MAP_FILE)
    testEvent = TestEvent(eventSvc)
    testEvent.startMonitoring(devID)

    doorSvc = DoorSvc(channel)
    accessSvc = AccessSvc(channel)
    userSvc = UserSvc(channel)
    TestDoor(doorSvc, accessSvc, userSvc, testEvent).test(devID)

    testEvent.stopMonitoring(devID)
    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the door test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   


if __name__ == '__main__':
    logging.basicConfig()
    test()
