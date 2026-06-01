import grpc
import display_pb2

def testDisplay(displaySvc, deviceID):
  try:
    displayConfig = displaySvc.getConfig(deviceID)

    print(f'\nDisplay config: \n{displayConfig}', flush=True)
  except grpc.RpcError as e:
    print(f'Cannot complete the display test: {e}')
