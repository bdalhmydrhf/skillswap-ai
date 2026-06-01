import grpc
import logging
import connect_pb2
import device_pb2

from testConfig import TestConfig

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.action.action import ActionSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.0.2'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.0.110'
DEVICE_PORT = 51211
USE_SSL = False

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

    actionSvc = ActionSvc(channel)
    TestConfig(actionSvc).test(devID)

    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the action test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   

if __name__ == '__main__':
    logging.basicConfig()
    test()
