import grpc

import card_pb2_grpc
import card_pb2


class CardSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = card_pb2_grpc.CardStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the card stub: {e}')
      raise

  def scan(self, deviceID):
    try:
      response = self.stub.Scan(card_pb2.ScanRequest(deviceID=deviceID))
      return response.cardData
    except grpc.RpcError as e:
      print(f'Cannot scan a card: {e}')
      raise

  def write(self, deviceID, smartCardData):
    try:
      self.stub.Write(card_pb2.WriteRequest(deviceID=deviceID, smartCardData=smartCardData))
    except grpc.RpcError as e:
      print(f'Cannot write a card: {e}')
      raise

  def writeQRCode(self, qrText):
    try:
      response = self.stub.WriteQRCode(card_pb2.WriteQRCodeRequest(QRText=qrText))
      return response.cardData
    except grpc.RpcError as e:
      print(f'Cannot write a QR code: {e}')
      raise

  def erase(self, deviceID):
    try:
      self.stub.Erase(card_pb2.EraseRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot erase a card: {e}')
      raise

  def getBlacklist(self, deviceID):
    try:
      response = self.stub.GetBlacklist(card_pb2.GetBlacklistRequest(deviceID=deviceID))
      return response.blacklist
    except grpc.RpcError as e:
      print(f'Cannot get the blacklist: {e}')
      raise

  def addBlacklist(self, deviceID, cardInfos):
    try:
      self.stub.AddBlacklist(card_pb2.AddBlacklistRequest(deviceID=deviceID, cardInfos=cardInfos))
    except grpc.RpcError as e:
      print(f'Cannot add the cards to the blacklist: {e}')
      raise

  def deleteBlacklist(self, deviceID, cardInfos):
    try:
      self.stub.DeleteBlacklist(card_pb2.DeleteBlacklistRequest(deviceID=deviceID, cardInfos=cardInfos))
    except grpc.RpcError as e:
      print(f'Cannot delete the cards from the blacklist: {e}')
      raise

  def deleteAllBlacklist(self, deviceID):
    try:
      self.stub.DeleteAllBlacklist(card_pb2.DeleteAllBlacklistRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all cards from the blacklist: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(card_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Card config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(card_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Card config: {e}')
      raise

  def get1xConfig(self, deviceID):
    try:
      response = self.stub.Get1XConfig(card_pb2.Get1XConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Card1x config: {e}')
      raise

  def set1xConfig(self, deviceID, config):
    try:
      self.stub.Set1XConfig(card_pb2.Set1XConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Card1x config: {e}')
      raise

  def getQRConfig(self, deviceID):
    try:
      response = self.stub.GetQRConfig(card_pb2.GetQRConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the QR config: {e}')
      raise

  def setQRConfig(self, deviceID, config):
    try:
      self.stub.SetQRConfig(card_pb2.SetQRConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the QR config: {e}')
      raise

  def getCustomConfig(self, deviceID):
    try:
      response = self.stub.GetCustomConfig(card_pb2.GetCustomConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the Custom config: {e}')
      raise

  def setCustomConfig(self, deviceID, config):
    try:
      self.stub.SetCustomConfig(card_pb2.SetCustomConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the Custom config: {e}')
      raise

  def getFacilityCodeConfig(self, deviceID):
    try:
      response = self.stub.GetFacilityCodeConfig(card_pb2.GetFacilityCodeConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the facility code config: {e}')
      raise

  def setFacilityCodeConfig(self, deviceID, config):
    try:
      self.stub.SetFacilityCodeConfig(card_pb2.SetFacilityCodeConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the facility code config: {e}')
      raise

  def getLockOverride(self, deviceID, lockOverrides):
    try:
      response = self.stub.GetLockOverride(card_pb2.GetLockOverrideRequest(deviceID=deviceID, lockOverrides=lockOverrides))
      return response.lockOverrides
    except grpc.RpcError as e:
      print(f'Cannot get lock overrides: {e}')
      raise

  def getAllLockOverride(self, deviceID):
    try:
      response = self.stub.GetAllLockOverride(card_pb2.GetAllLockOverrideRequest(deviceID=deviceID))
      return response.lockOverrides
    except grpc.RpcError as e:
      print(f'Cannot get all lock overrides: {e}')
      raise

  def setLockOverride(self, deviceID, lockOverrides):
    try:
      self.stub.SetLockOverride(card_pb2.SetLockOverrideRequest(deviceID=deviceID, lockOverrides=lockOverrides))
    except grpc.RpcError as e:
      print(f'Cannot set lock overrides: {e}')
      raise

  def deleteLockOverride(self, deviceID, lockOverrides):
    try:
      self.stub.DeleteLockOverride(card_pb2.DeleteLockOverrideRequest(deviceID=deviceID, lockOverrides=lockOverrides))
    except grpc.RpcError as e:
      print(f'Cannot delete lock overrides: {e}')
      raise

  def deleteAllLockOverride(self, deviceID):
    try:
      self.stub.DeleteAllLockOverride(card_pb2.DeleteAllLockOverrideRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all lock overrides: {e}')
      raise