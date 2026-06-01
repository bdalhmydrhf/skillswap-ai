import grpc
import threading

import connect_pb2

QUEUE_SIZE = 16

class DeviceMgr:
  connectSvc = None
  testConfig = None
  connectedIDs = []

  statusCh = None

  def __init__(self, connectSvc, testConfig): 
    self.connectSvc = connectSvc
    self.testConfig = testConfig

  def connectToDevices(self):
    connInfos = self.testConfig.getAsyncConnectInfo()
    try:
      self.connectSvc.addAsyncConnection(connInfos)
    except grpc.RpcError as e:
      print(f'Cannot add async connections: {e}')

  def getConnectedDevices(self, refreshList):
    try:
      if refreshList:
        devInfos = self.connectSvc.getDeviceList()
        self.connectedIDs.clear()        

        for dev in devInfos:
          if dev.status == connect_pb2.TCP_CONNECTED or dev.status == connect_pb2.TLS_CONNECTED:
            self.connectedIDs.append(dev.deviceID)        

      return self.connectedIDs
    except grpc.RpcError as e:
      print(f'Cannot get the connected devices: {e}')      

  def handleConnection(self, callback):
    try:
      self.statusCh = self.connectSvc.subscribe(QUEUE_SIZE)
      statusThread = threading.Thread(target=self.receiveStatus, args=(callback,))
      statusThread.start()
    except grpc.RpcError as e:
      print(f'Cannot subscribe to the device status channel: {e}')   

  def deleteConnection(self):
    try:
      if len(self.connectedIDs) > 0:
        self.connectSvc.deleteAsyncConnection(self.connectedIDs)
    except grpc.RpcError as e:
      print(f'Cannot delete async connection: {e}')   

  def updateConnectedIDs(self, devID):
    try:
      self.connectedIDs.index(devID)
    except ValueError:
      self.connectedIDs.append(devID)

  def receiveStatus(self, callback):
    try:
      for status in self.statusCh:
        if status.status == connect_pb2.DISCONNECTED:
          print(f'[DISCONNECTED] Device {status.deviceID}', flush=True)
          self.connectedIDs.remove(status.deviceID)
        elif status.status == connect_pb2.TLS_CONNECTED:
          print(f'[TLS_CONNECTED] Device {status.deviceID}', flush=True)
          self.updateConnectedIDs(status.deviceID)
          if not (callback is None):
            callback(status.deviceID)
        elif status.status == connect_pb2.TCP_CONNECTED:
          print(f'[TCP_CONNECTED] Device {status.deviceID}', flush=True)
          self.updateConnectedIDs(status.deviceID)
          if not (callback is None):
            callback(status.deviceID)
    
    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Subscription is cancelled', flush=True)    
      else:
        print(f'Cannot get the device status: {e}')   
