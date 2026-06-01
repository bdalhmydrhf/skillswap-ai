import grpc
import logging
import connect_pb2

from testEvent import TestEvent
from testConfig import TestConfig

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.tna.tna import TNASvc
from example.event.event import EventSvc
from example.device.device import DeviceSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.8.98'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.8.200'
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

    deviceSvc = DeviceSvc(channel)
    capability = deviceSvc.getCapability(devID)

    if not capability.displaySupported:
      raise Exception("The device does not support T&A")

    tnaSvc = TNASvc(channel)

    eventSvc = EventSvc(channel)
    eventSvc.initCodeMap(CODE_MAP_FILE)
    testEvent = TestEvent(eventSvc, tnaSvc)
    testEvent.startMonitoring(devID)
    
    testConfig = TestConfig(tnaSvc)
    origConfig = testConfig.test(devID)
    
    testEvent.test(devID)

    testEvent.stopMonitoring(devID)
    tnaSvc.setConfig(devID, origConfig)

    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the T&A test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   


if __name__ == '__main__':
    logging.basicConfig()
    test()
