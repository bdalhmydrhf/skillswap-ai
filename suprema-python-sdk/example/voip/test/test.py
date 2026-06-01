import grpc
import logging
import connect_pb2

from testConfig import TestConfig

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.voip.voip import VoipSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.8.98'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.8.227'
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

    voipSvc = VoipSvc(channel)
    voipConfig = voipSvc.getConfig(devID)
    print(f'\nOriginal Voip Config: \n{voipConfig}', flush=True)
    
    testConfig = TestConfig(voipSvc)
    testConfig.test(devID, voipConfig)

    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the voip test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   


if __name__ == '__main__':
    logging.basicConfig()
    test()
