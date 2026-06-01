import grpc
import json
import sys

import server_pb2_grpc
import server_pb2


class ServerSvc:
  stub = None
  codeMap = None

  def __init__(self, channel): 
    try:
      self.stub = server_pb2_grpc.ServerStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the server stub: {e}')
      raise

  def subscribe(self, queueSize): 
    try:
      return self.stub.Subscribe(server_pb2.SubscribeRequest(queueSize=queueSize))
    except grpc.RpcError as e:
      print(f'Cannot subscribe: {e}')
      raise

  def unsubscribe(self): 
    try:
      self.stub.Unsubscribe(server_pb2.UnsubscribeRequest())
    except grpc.RpcError as e:
      print(f'Cannot unsubscribe: {e}')
      raise

  def handleVerify(self, serverReq, errCode, userInfo):
    try:
      self.stub.HandleVerify(server_pb2.HandleVerifyRequest(deviceID=serverReq.deviceID, seqNO=serverReq.seqNO, errCode=errCode, user=userInfo))
    except grpc.RpcError as e:
      print(f'Cannot handle verify: {e}')
      raise

  def handleIdentify(self, serverReq, errCode, userInfo):
    try:
      self.stub.HandleIdentify(server_pb2.HandleIdentifyRequest(deviceID=serverReq.deviceID, seqNO=serverReq.seqNO, errCode=errCode, user=userInfo))
    except grpc.RpcError as e:
      print(f'Cannot handle identify: {e}')
      raise
