import grpc
import schedule_pb2
from datetime import datetime
from example.cli.input import UserInput

SAMPLE_HOLIDAY_GROUP_ID = 1
WEEKLY_SCHEDULE_ID = 2 # 0 and 1 are reserved
DAILY_SCHEDULE_ID = WEEKLY_SCHEDULE_ID + 1
NUM_OF_DAY = 30

class TestSample:
  scheduleSvc = None

  def __init__(self, svc): 
    self.scheduleSvc = svc

  def test(self, deviceID):
    try:
      # Backup the original schedules
      origSchedules = self.scheduleSvc.getList(deviceID)
      origHolidayGroups = self.scheduleSvc.getHolidayList(deviceID)

      print(f'Original Schedules: \n{origSchedules}\n', flush=True)
      print(f'Original Holiday Groups: \n{origHolidayGroups}\n', flush=True)

      print(f'\n===== Test Sample Schedules =====\n', flush=True)
      self.scheduleSvc.deleteAll(deviceID)
      self.scheduleSvc.deleteAllHoliday(deviceID)

      holidaySchedule = self.makeHolidayGroup(deviceID)
      self.makeWeeklySchedule(deviceID, holidaySchedule)
      self.makeDailySchedule(deviceID)

      newSchedules = self.scheduleSvc.getList(deviceID)
      newHolidayGroups = self.scheduleSvc.getHolidayList(deviceID)

      print(f'>>> Sample Schedules: \n{newSchedules}\n', flush=True)
      print(f'>>> Sample Holiday Groups: \n{newHolidayGroups}\n', flush=True)

      UserInput.pressEnter('>> Press ENTER to finish the test.\n')       

      # Restore the original schedules
      self.scheduleSvc.deleteAll(deviceID)
      self.scheduleSvc.deleteAllHoliday(deviceID)
      if len(origSchedules) > 0:
        self.scheduleSvc.add(deviceID, origSchedules)
      if len(origHolidayGroups) > 0:
        self.scheduleSvc.addHoliday(deviceID, origHolidayGroups)

    except grpc.RpcError as e:
      print(f'Cannot finish the sample test: {e}', flush=True)
      raise

  def makeHolidayGroup(self, deviceID):
    try:
      jan1st = schedule_pb2.Holiday(date=0, recurrence=schedule_pb2.RECUR_YEARLY) # Jan. 1st
      dec25th = schedule_pb2.Holiday(date=358, recurrence=schedule_pb2.RECUR_YEARLY) # Dec. 25th in non leap year, 359 in leap year
      holidayGroup = schedule_pb2.HolidayGroup(ID=SAMPLE_HOLIDAY_GROUP_ID, name='Sample Holiday Group', holidays=[jan1st, dec25th])

      self.scheduleSvc.addHoliday(deviceID, [holidayGroup])

      holidayDaySchedule = schedule_pb2.DaySchedule()
      holidayDaySchedule.periods.append(schedule_pb2.TimePeriod(startTime=600, endTime=720)) # // 10 am ~ 12 pm

      holidaySchedule = schedule_pb2.HolidaySchedule(groupID=SAMPLE_HOLIDAY_GROUP_ID, daySchedule=holidayDaySchedule)

      return holidaySchedule

    except grpc.RpcError as e:
      print(f'Cannot make a holiday group: {e}', flush=True)
      raise

  def makeWeeklySchedule(self, deviceID, holidaySchedule):
    try:
      weekdaySchedule = schedule_pb2.DaySchedule()
      weekdaySchedule.periods.append(schedule_pb2.TimePeriod(startTime=540, endTime=720)) # 9 am ~ 12 pm
      weekdaySchedule.periods.append(schedule_pb2.TimePeriod(startTime=780, endTime=1080)) # 1 pm ~ 6 pm

      weekendSchedule = schedule_pb2.DaySchedule()
      weekendSchedule.periods.append(schedule_pb2.TimePeriod(startTime=570, endTime=770)) # 9:30 am ~ 12:30 pm

      weeklySchedule = schedule_pb2.WeeklySchedule()
      weeklySchedule.daySchedules.append(weekendSchedule) # Sunday
      weeklySchedule.daySchedules.append(weekdaySchedule) # Monday
      weeklySchedule.daySchedules.append(weekdaySchedule) # Tuessay
      weeklySchedule.daySchedules.append(weekdaySchedule) # Wednesday
      weeklySchedule.daySchedules.append(weekdaySchedule) # Thursday
      weeklySchedule.daySchedules.append(weekdaySchedule) # Friday
      weeklySchedule.daySchedules.append(weekendSchedule) # Saturday

      scheduleInfo = schedule_pb2.ScheduleInfo(ID=WEEKLY_SCHEDULE_ID, name='Sample Weekly Schedule', weekly=weeklySchedule, holidays=[holidaySchedule])

      self.scheduleSvc.add(deviceID, [scheduleInfo])

    except grpc.RpcError as e:
      print(f'Cannot make a weekly schedule: {e}', flush=True)
      raise

  def makeDailySchedule(self, deviceID):
    try:
      daySchedule = schedule_pb2.DaySchedule()
      daySchedule.periods.append(schedule_pb2.TimePeriod(startTime=540, endTime=720)) # 9 am ~ 12 pm
      daySchedule.periods.append(schedule_pb2.TimePeriod(startTime=780, endTime=1080)) # 1 pm ~ 6 pm

      dailySchedule = schedule_pb2.DailySchedule(startDate=int(datetime.now().strftime('%j')) - 1) # 30 days starting from today
      for i in range(NUM_OF_DAY):
        dailySchedule.daySchedules.append(daySchedule)

      scheduleInfo = schedule_pb2.ScheduleInfo(ID=DAILY_SCHEDULE_ID, name='Sample Daily Schedule', daily=dailySchedule)

      self.scheduleSvc.add(deviceID, [scheduleInfo])
    
    except grpc.RpcError as e:
      print(f'Cannot make a daily schedule: {e}', flush=True)
      raise
