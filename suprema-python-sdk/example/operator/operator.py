import grpc

import operator_pb2_grpc
import operator_pb2


class OperatorSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = operator_pb2_grpc.OperatorStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the operator stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(operator_pb2.GetListRequest(deviceID=deviceID))
      return response.operators
    except grpc.RpcError as e:
      print(f'Cannot get the operator list: {e}')
      raise

  def add(self, deviceID, operators):
    try:
      self.stub.Add(operator_pb2.AddRequest(deviceID=deviceID, operators=operators))
    except grpc.RpcError as e:
      print(f'Cannot add operators: {e}')
      raise

  def delete(self, deviceID, operatorIDs):
    try:
      self.stub.Delete(operator_pb2.DeleteRequest(deviceID=deviceID, operatorIDs=operatorIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete operators: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(operator_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the operators: {e}')
      raise
