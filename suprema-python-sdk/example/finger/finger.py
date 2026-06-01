import grpc

import finger_pb2_grpc
import finger_pb2


class FingerSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = finger_pb2_grpc.FingerStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the finger stub: {e}')
      raise

  def scan(self, deviceID, templateFormat, qualityThreshold):
    try:
      response = self.stub.Scan(finger_pb2.ScanRequest(deviceID=deviceID, templateFormat=templateFormat, qualityThreshold=qualityThreshold))
      return response.templateData
    except grpc.RpcError as e:
      print(f'Cannot scan a finger: {e}')
      raise

  def verify(self, deviceID, fingerData):
    try:
      self.stub.Verify(finger_pb2.VerifyRequest(deviceID=deviceID, fingerData=fingerData))
      return
    except grpc.RpcError as e:
      print(f'Cannot verify the fingerprints: {e}')
      raise

  def getImage(self, deviceID):
    try:
      response = self.stub.GetImage(finger_pb2.GetImageRequest(deviceID=deviceID))
      return response.BMPImage
    except grpc.RpcError as e:
      print(f'Cannot get the fingerprint image: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(finger_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Fingerprint config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(finger_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Fingerprint config: {e}')
      raise
