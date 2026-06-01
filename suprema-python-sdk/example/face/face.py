import grpc

import face_pb2_grpc
import face_pb2


class FaceSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = face_pb2_grpc.FaceStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the face stub: {e}')
      raise

  def scan(self, deviceID, enrollThreshold):
    try:
      response = self.stub.Scan(face_pb2.ScanRequest(deviceID=deviceID, enrollThreshold=enrollThreshold))
      return response.faceData
    except grpc.RpcError as e:
      print(f'Cannot scan a face: {e}')
      raise

  def normalize(self, deviceID, unwrappedImageData):
    try:
      response = self.stub.Normalize(face_pb2.NormalizeRequest(deviceID=deviceID, unwrappedImageData=unwrappedImageData))
      return response.wrappedImageData
    except grpc.RpcError as e:
      print(f'Cannot normalize a face: {e}')
      raise    

  def extract(self, deviceID, imageData, isWarped):
    try:
      response = self.stub.Extract(face_pb2.ExtractRequest(deviceID=deviceID, imageData=imageData, isWarped=isWarped))
      return response.templateData
    except grpc.RpcError as e:
      print(f'Cannot extract a face: {e}')
      raise    

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(face_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Face config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(face_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Face config: {e}')
      raise

  def getAuthGroup(self, deviceID):
    try:
      response = self.stub.GetAuthGroup(face_pb2.GetAuthGroupRequest(deviceID=deviceID))
      return response.authGroups
    except grpc.RpcError as e:
      print(f'Cannot get auth groups: {e}')
      raise

  def addAuthGroup(self, deviceID, groups):
    try:
      self.stub.AddAuthGroup(face_pb2.AddAuthGroupRequest(deviceID=deviceID, authGroups=groups))
    except grpc.RpcError as e:
      print(f'Cannot add auth groups: {e}')
      raise

  def deleteAuthGroup(self, deviceID, groupIDs):
    try:
      self.stub.DeleteAuthGroup(face_pb2.DeleteAuthGroupRequest(deviceID=deviceID, groupIDs=groupIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete auth groups: {e}')
      raise

  def deleteAllAuthGroup(self, deviceID):
    try:
      self.stub.DeleteAllAuthGroup(face_pb2.DeleteAllAuthGroupRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all auth groups: {e}')
      raise
