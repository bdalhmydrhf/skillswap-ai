import grpc

import schedule_pb2_grpc
import schedule_pb2


class ScheduleSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = schedule_pb2_grpc.ScheduleStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the schedule stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(schedule_pb2.GetListRequest(deviceID=deviceID))
      return response.schedules
    except grpc.RpcError as e:
      print(f'Cannot get the schedule list: {e}')
      raise

  def add(self, deviceID, schedules):
    try:
      self.stub.Add(schedule_pb2.AddRequest(deviceID=deviceID, schedules=schedules))
    except grpc.RpcError as e:
      print(f'Cannot add schedules: {e}')
      raise

  def delete(self, deviceID, scheduleIDs):
    try:
      self.stub.Delete(schedule_pb2.DeleteRequest(deviceID=deviceID, scheduleIDs=scheduleIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete schedules: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(schedule_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the schedules: {e}')
      raise

  def getHolidayList(self, deviceID):
    try:
      response = self.stub.GetHolidayList(schedule_pb2.GetHolidayListRequest(deviceID=deviceID))
      return response.groups
    except grpc.RpcError as e:
      print(f'Cannot get the holiday list: {e}')
      raise

  def addHoliday(self, deviceID, groups):
    try:
      self.stub.AddHoliday(schedule_pb2.AddHolidayRequest(deviceID=deviceID, groups=groups))
    except grpc.RpcError as e:
      print(f'Cannot add holiday groups: {e}')
      raise

  def deleteHoliday(self, deviceID, groupIDs):
    try:
      self.stub.DeleteHoliday(schedule_pb2.DeleteHolidayRequest(deviceID=deviceID, groupIDs=groupIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete holiday groups: {e}')
      raise

  def deleteAllHoliday(self, deviceID):
    try:
      self.stub.DeleteAllHoliday(schedule_pb2.DeleteAllHolidayRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all the holiday groups: {e}')
      raise

