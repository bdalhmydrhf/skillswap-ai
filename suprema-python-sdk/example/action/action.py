import grpc

import action_pb2_grpc
import action_pb2


class ActionSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = action_pb2_grpc.TriggerActionStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the action stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(action_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the action config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(action_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the action config: {e}')
      raise

  def runAction(self, deviceID, action):
    try:
      self.stub.RunAction(action_pb2.RunActionRequest(deviceID=deviceID, action=action))
    except grpc.RpcError as e:
      print(f'Cannot run the action: {e}')
      raise