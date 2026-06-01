import grpc
import face_pb2

IMAGE_FILENAME = './face.bmp'

def testFace(faceSvc, deviceID):
  try:
    faceConfig = faceSvc.getConfig(deviceID)

    print(f'\nFace config: \n{faceConfig}', flush=True)

    print('>>> Scan a face...', flush=True)

    faceData = faceSvc.scan(deviceID, faceConfig.enrollThreshold)

    for i in range(len(faceData.templates)):
      print(f'Template data[{i}]: {faceData.templates[i]}', flush=True)

    f = open(IMAGE_FILENAME, 'wb')
    f.write(faceData.imageData)
    f.close()
  except grpc.RpcError as e:
    print(f'Cannot complete the face test: {e}')
