import grpc
import logging
import connect_pb2
import device_pb2

from testConfig import TestConfig

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.status.status import StatusSvc
from example.device.device import DeviceSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.8.98'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.8.205'
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

    deviceSvc = DeviceSvc(channel)
    capability = deviceSvc.getCapability(devID)

    if capability.displaySupported:
      print(f'Status configuration is effective only for headless devices: {capability.displaySupported}', flush=True)
      connectSvc.disconnect([devID])
      channel.close() 
      return


    statusSvc = StatusSvc(channel)
    TestConfig(statusSvc).test(devID)

    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the status test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   

def isHeadless(devType):
  headlessTypes = [
    device_pb2.BIOENTRY_P2, 
    device_pb2.BIOENTRY_R2, 
    device_pb2.BIOENTRY_W2, 
    device_pb2.XPASS2, 
    device_pb2.XPASS2_KEYPAD, 
    device_pb2.XPASS_D2, 
    device_pb2.XPASS_D2_KEYPAD, 
    device_pb2.XPASS_S2
  ]

  for headlessType in headlessTypes:
    if devType == headlessType:
      return True

  return False

if __name__ == '__main__':
    logging.basicConfig()
    test()
