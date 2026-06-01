import grpc
import time
import auth_pb2
import device_pb2

from example.cli.input import UserInput

class TestAuth:
  authSvc = None

  def __init__(self, authSvc): 
    self.authSvc = authSvc

  def prepareAuthConfig(self, deviceID):
    try:
      config = self.authSvc.getConfig(deviceID)

      # Backup the original configuration
      origConfig = auth_pb2.AuthConfig()
      origConfig.CopyFrom(config)

      # Enable private authentication for test
      config.usePrivateAuth = True
      self.authSvc.setConfig(deviceID, config)

      return origConfig
    except grpc.RpcError as e:
      print(f'Cannot get the auth config: {e}', flush=True)   
      raise

  def test(self, deviceID, extendedAuthSupported):
    try:
      print(f'\n===== Auth Mode Test =====\n', flush=True)

      config = auth_pb2.AuthConfig(matchTimeout=10, authTimeout=15, usePrivateAuth=False)

      if extendedAuthSupported:
        config.authSchedules.add(mode=auth_pb2.AUTH_EXT_MODE_CARD_ONLY, scheduleID=1) # Card Only, Always
        config.authSchedules.add(mode=auth_pb2.AUTH_EXT_MODE_FACE_ONLY, scheduleID=1) # Face Only, Always
        config.authSchedules.add(mode=auth_pb2.AUTH_EXT_MODE_FINGERPRINT_ONLY, scheduleID=1) # Fingerprint Only, Always
      else:
        config.authSchedules.add(mode=auth_pb2.AUTH_MODE_CARD_ONLY, scheduleID=1) # Card Only, Always
        config.authSchedules.add(mode=auth_pb2.AUTH_MODE_BIOMETRIC_ONLY, scheduleID=1) # Biometric Only, Always

      self.authSvc.setConfig(deviceID, config)

      UserInput.pressEnter('>> Try to authenticate card or fingerprint or face. And, press ENTER for the next test.\n')

      del config.authSchedules[:]

      if extendedAuthSupported:
        config.authSchedules.add(mode=auth_pb2.AUTH_EXT_MODE_CARD_FACE, scheduleID=1) # Card + Face, Always
        config.authSchedules.add(mode=auth_pb2.AUTH_EXT_MODE_CARD_FINGERPRINT, scheduleID=1) # Card + Fingerprint, Always
      else:
        config.authSchedules.add(mode=auth_pb2.AUTH_MODE_CARD_BIOMETRIC, scheduleID=1) # Card + Biometric, Always

      self.authSvc.setConfig(deviceID, config)

      UserInput.pressEnter('>> Try to authenticate (card + fingerprint) or (card + face). And, press ENTER for the next test.\n')

    except grpc.RpcError as e:
      print(f'Cannot finish the auth mode test: {e}', flush=True)   
      raise