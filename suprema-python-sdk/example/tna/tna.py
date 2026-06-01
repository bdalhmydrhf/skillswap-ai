import grpc

import tna_pb2_grpc
import tna_pb2


class TNASvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = tna_pb2_grpc.TNAStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the tna stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(tna_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the tna config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(tna_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the tna config: {e}')
      raise

  def getTNALog(self, deviceID, startEventID, maxNumOfLog):
    try:
      response = self.stub.GetTNALog(tna_pb2.GetTNALogRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog))
      return response.TNAEvents
    except grpc.RpcError as e:
      print(f'Cannot get the TNA event log: {e}')
      raise

  def getJobCodeLog(self, deviceID, startEventID, maxNumOfLog):
    try:
      response = self.stub.GetJobCodeLog(tna_pb2.GetJobCodeLogRequest(deviceID=deviceID, startEventID=startEventID, maxNumOfLog=maxNumOfLog))
      return response.jobCodeEvents
    except grpc.RpcError as e:
      print(f'Cannot get the JobCode event log: {e}')
      raise
