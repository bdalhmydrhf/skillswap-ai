import grpc

import test_pb2_grpc
import test_pb2


class TestSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = test_pb2_grpc.TestStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the test stub: {e}')
      raise

  def detectCard(self, deviceID, cardData):
    try:
      self.stub.DetectCard(test_pb2.DetectCardRequest(deviceID=deviceID, cardData=cardData))
    except grpc.RpcError as e:
      print(f'Cannot detect card: {e}')
      raise

  def detectFace(self, deviceID, faceTemplate):
    try:
      self.stub.DetectFace(test_pb2.DetectFaceRequest(deviceID=deviceID, faceTemplate=faceTemplate))
    except grpc.RpcError as e:
      print(f'Cannot detect face: {e}')
      raise

  def detectFingerprint(self, deviceID, fingerprintTemplate):
    try:
      self.stub.DetectFingerprint(test_pb2.DetectFingerprintRequest(deviceID=deviceID, fingerprintTemplate=fingerprintTemplate))
    except grpc.RpcError as e:
      print(f'Cannot detect fingerprint: {e}')
      raise

  def enterKey(self, deviceID, input):
    try:
      self.stub.EnterKey(test_pb2.EnterKeyRequest(deviceID=deviceID, input=input))
    except grpc.RpcError as e:
      print(f'Cannot enter key: {e}')
      raise
