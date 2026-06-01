import grpc

def testDevice(deviceSvc, deviceID):
  try:
    info = deviceSvc.getInfo(deviceID)

    print(f'Device info: \n{info}', flush=True)

    capabilityInfo = deviceSvc.getCapInfo(deviceID)

    print(f'Capability info: \n{capabilityInfo}', flush=True)
    return capabilityInfo

  except grpc.RpcError as e:
    print(f'Cannot complete the device test: {e}')
