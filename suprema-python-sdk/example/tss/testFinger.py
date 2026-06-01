import grpc
import finger_pb2

QUALITY_THRESHOLD = 50
IMAGE_FILENAME = './finger.bmp'

def testFinger(fingerSvc, deviceID):
  try:
    fingerConfig = fingerSvc.getConfig(deviceID)
    print(f'\nFingerprint config: \n{fingerConfig}', flush=True)

    print('>>> Scan a finger...', flush=True)

    templateData = fingerSvc.scan(deviceID, fingerConfig.templateFormat, QUALITY_THRESHOLD)
    print(f'Template data: {templateData}', flush=True)

    fingerImage = fingerSvc.getImage(deviceID)
    f = open(IMAGE_FILENAME, 'wb')
    f.write(fingerImage)
    f.close()

 
  except grpc.RpcError as e:
    print(f'Cannot complete the finger test: {e}')
