import grpc
import connect_pb2

def testConnect(connectSvc, ipAddr, port, useSSL):
  try:
    connInfo = connect_pb2.ConnectInfo(IPAddr=ipAddr, port=port, useSSL=useSSL)

    devID = connectSvc.connect(connInfo)

    devList = connectSvc.getDeviceList()
    print(f'Device list: {devList}', flush=True)

    return devID

  except grpc.RpcError as e:
    print(f'Cannot complete the connect test: {e}')

def testConnectMaster(connectMasterSvc, gatewayID, ipAddr, port, useSSL):
  try:
    connInfo = connect_pb2.ConnectInfo(IPAddr=ipAddr, port=port, useSSL=useSSL)

    devID = connectMasterSvc.connect(gatewayID, connInfo)

    devList = connectMasterSvc.getDeviceList(gatewayID)
    print(f'Device list: {devList}', flush=True)

    return devID

  except grpc.RpcError as e:
    print(f'Cannot complete the connect test: {e}')    
