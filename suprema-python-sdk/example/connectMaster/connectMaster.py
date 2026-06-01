import grpc

import connect_master_pb2_grpc
import connect_master_pb2


class ConnectMasterSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = connect_master_pb2_grpc.ConnectMasterStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the connectMaster stub: {e}', flush=True)
      raise

  def searchDevice(self, gatewayID, timeout):
    try:
      response = self.stub.SearchDevice(connect_master_pb2.SearchDeviceRequest(gatewayID=gatewayID, timeout=timeout))
      return response.deviceInfos
    except grpc.RpcError as e:
      print(f'Cannot search devices: {e}', flush=True)
      raise

  def getDeviceList(self, gatewayID):
    try:
      response = self.stub.GetDeviceList(connect_master_pb2.GetDeviceListRequest(gatewayID=gatewayID))
      return response.deviceInfos
    except grpc.RpcError as e:
      print(f'Cannot get the device list: {e}', flush=True)
      raise

  def getSlaveDevice(self, gatewayID):
    try:
      response = self.stub.GetSlaveDevice(connect_master_pb2.GetSlaveDeviceRequest(gatewayID=gatewayID))
      return response.slaveDeviceInfos
    except grpc.RpcError as e:
      print(f'Cannot get slave devices: {e}', flush=True)
      raise

  def setSlaveDevice(self, gatewayID, slaves):
    try:
      self.stub.SetSlaveDevice(connect_master_pb2.SetSlaveDeviceRequest(gatewayID=gatewayID, slaveDeviceInfos=slaves))
    except grpc.RpcError as e:
      print(f'Cannot set slave devices: {e}', flush=True)
      raise

  def addSlaveDeviceDB(self, gatewayID, slaves):
    try:
      self.stub.AddSlaveDeviceDB(connect_master_pb2.AddSlaveDeviceDBRequest(gatewayID=gatewayID, slaveDeviceInfos=slaves))
    except grpc.RpcError as e:
      print(f'Cannot add slave devices on database: {e}', flush=True)
      raise

  def deleteSlaveDeviceDB(self, gatewayID, deviceIDs):
    try:
      self.stub.DeleteSlaveDeviceDB(connect_master_pb2.DeleteSlaveDeviceDBRequest(gatewayID=gatewayID, deviceIDs=deviceIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete slave devices on database: {e}', flush=True)
      raise

  def getSlaveDeviceDB(self, gatewayID):
    try:
      response = self.stub.GetSlaveDeviceDB(connect_master_pb2.GetSlaveDeviceDBRequest(gatewayID=gatewayID))
      return response.slaveDeviceInfos
    except grpc.RpcError as e:
      print(f'Cannot get slave devices on database: {e}', flush=True)
      raise

  def connect(self, gatewayID, connInfo):
    try:
      response = self.stub.Connect(connect_master_pb2.ConnectRequest(gatewayID=gatewayID, connectInfo=connInfo))
      return response.deviceID
    except grpc.RpcError as e:
      print(f'Cannot connect to the device: {e}', flush=True)
      raise

  def disconnect(self, deviceIDs):
    try:
      self.stub.Disconnect(connect_master_pb2.DisconnectRequest(deviceIDs=deviceIDs))
    except grpc.RpcError as e:
      print(f'Cannot disconnect devices: {e}', flush=True)
      raise

  def disconnectAll(self, gatewayID):
    try:
      self.stub.DisconnectAll(connect_master_pb2.DisconnectAllRequest(gatewayID=gatewayID))
    except grpc.RpcError as e:
      print(f'Cannot disconnect all devices: {e}', flush=True)
      raise

  def addAsyncConnection(self, gatewayID, connInfos):
    try:
      self.stub.AddAsyncConnection(connect_master_pb2.AddAsyncConnectionRequest(gatewayID=gatewayID, connectInfos=connInfos))
    except grpc.RpcError as e:
      print(f'Cannot add async connections: {e}', flush=True)
      raise

  def deleteAsyncConnection(self, gatewayID, deviceIDs):
    try:
      self.stub.DeleteAsyncConnection(connect_master_pb2.DeleteAsyncConnectionRequest(gatewayID=gatewayID, deviceIDs=deviceIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete async connections: {e}', flush=True)
      raise    

  def getPendingList(self, gatewayID):
    try:
      response = self.stub.GetPendingList(connect_master_pb2.GetPendingListRequest(gatewayID=gatewayID))
      return response.deviceInfos
    except grpc.RpcError as e:
      print(f'Cannot get the pending list: {e}', flush=True)
      raise    

  def getAcceptFilter(self, gatewayID):
    try:
      response = self.stub.GetAcceptFilter(connect_master_pb2.GetAcceptFilterRequest(gatewayID=gatewayID))
      return response.filter
    except grpc.RpcError as e:
      print(f'Cannot get the accept filter: {e}', flush=True)
      raise      

  def setAcceptFilter(self, gatewayID, filter):
    try:
      self.stub.SetAcceptFilter(connect_master_pb2.SetAcceptFilterRequest(gatewayID=gatewayID, filter=filter))      
    except grpc.RpcError as e:
      print(f'Cannot set the accept filter: {e}', flush=True)
      raise 

  def setConnectionMode(self, deviceIDs, mode):
    try:
      self.stub.SetConnectionModeMulti(connect_master_pb2.SetConnectionModeMultiRequest(deviceIDs=deviceIDs, connectionMode=mode))
    except grpc.RpcError as e:
      print(f'Cannot set the connection mode: {e}', flush=True)
      raise 

  def enableSSL(self, deviceIDs):
    try:
      self.stub.EnableSSLMulti(connect_master_pb2.EnableSSLMultiRequest(deviceIDs=deviceIDs))
    except grpc.RpcError as e:
      print(f'Cannot enable SSL: {e}', flush=True)
      raise 

  def disableSSL(self, deviceIDs):
    try:
      self.stub.DisableSSLMulti(connect_master_pb2.DisableSSLMultiRequest(deviceIDs=deviceIDs))
    except grpc.RpcError as e:
      print(f'Cannot disable SSL: {e}', flush=True)
      raise 

  def subscribe(self, queueSize):
    try:
      return self.stub.SubscribeStatus(connect_master_pb2.SubscribeStatusRequest(queueSize=queueSize))
    except grpc.RpcError as e:
      print(f'Cannot subscribe: {e}', flush=True)
      raise
