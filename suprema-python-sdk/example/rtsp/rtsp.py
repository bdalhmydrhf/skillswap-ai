import grpc

import rtsp_pb2_grpc
import rtsp_pb2


class RtspSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = rtsp_pb2_grpc.RTSPStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the rtsp stub: {e}')
      raise

  def getConfig(self, deviceID):
    try:
      response = self.stub.GetConfig(rtsp_pb2.GetConfigRequest(deviceID=deviceID))
      return response.config
    except grpc.RpcError as e:
      print(f'Cannot get the rtsp config: {e}')
      raise

  def setConfig(self, deviceID, config):
    try:
      self.stub.SetConfig(rtsp_pb2.SetConfigRequest(deviceID=deviceID, config=config))
    except grpc.RpcError as e:
      print(f'Cannot set the rtsp config: {e}')
      raise
