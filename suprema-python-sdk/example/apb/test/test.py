import grpc
import logging
import connect_pb2

from testEvent import TestEvent
from testAPBZone import TestAPBZone
from testRS485 import TestRS485

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.event.event import EventSvc
from example.apb.apb import APBZoneSvc
from example.rs485.rs485 import RS485Svc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.0.2'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.0.120'
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

    rs485Svc = RS485Svc(channel)
    rs485Test = TestRS485(rs485Svc)
    hasSlave = rs485Test.checkSlaves(devID)
    if not hasSlave:
      connectSvc.disconnect([devID])
      channel.close()  
      return

    eventSvc = EventSvc(channel)
    eventSvc.initCodeMap(CODE_MAP_FILE)
    testEvent = TestEvent(eventSvc)
    testEvent.startMonitoring(devID)

    apbSvc = APBZoneSvc(channel)
    TestAPBZone(apbSvc).test(devID, rs485Test.getSlaves())

    rs485Test.restoreSlaves(devID)
    testEvent.stopMonitoring(devID)
    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the apb test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   

    if hasSlave:
      rs485Test.restoreSlaves(devID)


if __name__ == '__main__':
    logging.basicConfig()
    test()
