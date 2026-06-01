import enum
import input_pb2
import device_pb2
import rs485_pb2
import card_pb2
import user_pb2
import auth_pb2
from typing import List, Optional

from example.connect.connect import ConnectSvc
from example.device.device import DeviceSvc
from example.rs485.rs485 import RS485Svc
from example.input.input import InputSvc
from example.card.card import CardSvc
from example.user.user import UserSvc

def printFields(pb_obj):
    from google.protobuf.descriptor import FieldDescriptor

    print(f"--- {pb_obj.__class__.__name__} ---")
    for field in pb_obj.DESCRIPTOR.fields:
        value = getattr(pb_obj, field.name)

        if field.type == FieldDescriptor.TYPE_ENUM:
            enum_name = field.enum_type.values_by_number.get(value)
            if enum_name:
                value = f"{enum_name.name} ({value})"
        
        print(f"{field.name}: {value}")

def getInput(prompt, default):
    userInput = input(f"{prompt} (default: {default}): ") or default
    if userInput == "":
        return default
    try:
        return type(default)(userInput)
    except ValueError:
        print(f"Invalid input. Returning default value: {default}")
        return default

def getTypeName(type):
  try:
    return device_pb2.Type.Name(type)
  except ValueError as e:
    return device_pb2.Type.Name(device_pb2.UNKNOWN)


class SlaveFilter(enum.Enum):
    ALL = 0
    PANEL = 1
    DI24 = 2
    SLAVE = 3


class CS20485Test:
    TEST_USER_STARTTIME = 946684800
    TEST_USER_ENDTIME = 1924991999

    def __init__(self, connectSvc, deviceSvc, rs485Svc, inputSvc, cardSvc, userSvc):
        self.connectSvc_ = connectSvc
        self.deviceSvc_ = deviceSvc
        self.rs485Svc_ = rs485Svc
        self.inputSvc_ = inputSvc
        self.cardSvc_ = cardSvc
        self.userSvc_ = userSvc

    def getChannelString(self, mode):
        return {rs485_pb2.MASTER: "M", rs485_pb2.STANDALONE: "A", rs485_pb2.SLAVE: "S"}.get(mode, "N")

    def showSlaveInfo(self, channel, filter):
        for slave in channel.slaveDevices:
            if (
                filter == SlaveFilter.ALL
                or (
                    filter == SlaveFilter.PANEL
                    and channel.mode in [rs485_pb2.MASTER]
                    and slave.type in [device_pb2.CORESTATION_40, device_pb2.CORESTATION_20, device_pb2.DOOR_INTERFACE_24]
                )
                or (filter == SlaveFilter.DI24 and slave.type == device_pb2.DOOR_INTERFACE_24)
                or (filter == SlaveFilter.SLAVE and slave.parentID > 0)
            ):
                status = "(+)" if slave.connected else "(-)"
                print(f"[{self.getChannelString(channel.mode)}] {status} {slave.deviceID}, {getTypeName(slave.type)}, {slave.parentID}")

    def showSlaves(self, deviceID, filter):
        rs485Config = self.rs485Svc_.getConfig(deviceID)
        if not rs485Config:
            print("Failed to get RS485 config.")
            return

        for channel in rs485Config.channels:
            self.showSlaveInfo(channel, filter)

    def selectDeviceId(self, prompt, deviceID, filter):
        if filter in [SlaveFilter.ALL, SlaveFilter.PANEL]:
            capInfo = self.deviceSvc_.getCapInfo(deviceID)
            if not capInfo:
                print("Failed to get capability info.")
                return 0
            print(f"[M] {deviceID} {getTypeName(capInfo.type)}")

        self.showSlaves(deviceID, filter)
        return int(input(f"{prompt} (default: 0): ") or 0)

    def searchSlave(self, deviceID):
        masterID = self.selectDeviceId(
            "Enter Master ID: ", deviceID, SlaveFilter.PANEL
        )
        if masterID == 0:
            print("Invalid Master ID.")
            return

        slaveInfos = self.rs485Svc_.searchSlave(masterID)
        if not slaveInfos:
            print("Failed to search slaves.")
            return

        print("===== Slave list =====")
        for slaveInfo in slaveInfos:
            print(slaveInfo)
            slaveInfo.enabled = True

        register = int(input("Register All. (1: Yes, 0: No): ") or 1)
        if register == 1:
            self.rs485Svc_.setSlave(masterID, slaveInfos)
            slaveDeviceList = self.getSlaveDeviceInfo()
            if slaveDeviceList:
                self.connectSvc_.setSlaveDevice(slaveDeviceList)

    def getSlaveDeviceInfo(self):
        slaveInfos = []
        devList = self.connectSvc_.getDeviceList()
        if not devList:
            print("Cannot get device list.")
            return None

        for devInfo in devList:
            rs485Config = self.rs485Svc_.getConfig(devInfo.deviceID)
            if not rs485Config:
                print(f"Cannot get RS485 config for device {devInfo.deviceID}")
                continue

            slaveItem = {"deviceID": devInfo.deviceID, "rs485SlaveDeviceIDs": []}
            for channel in rs485Config.channels:
                for slave in channel.slaveDevices:
                    if slave.enabled:
                        slaveItem["rs485SlaveDeviceIDs"].append(slave.deviceID)

            slaveInfos.append(slaveItem)

        return slaveInfos

    def getInputConfig(self, device_id):
        panelID = self.selectDeviceId("Enter Panel ID: ", device_id, SlaveFilter.PANEL)
        if panelID == 0:
            print("Invalid Panel ID.")
            return

        inputConfig = self.inputSvc_.getConfig(panelID)
        if inputConfig is None:
            print("Failed to get input config.")
            return

        print("===== Input config =====")
        print(f"AuxInput: {inputConfig.auxInput}")
        for i, sInput in enumerate(inputConfig.supervisedInputs):
            print(f"Supervised[{i}]: {sInput}")

    def selectAuxInputPort(self, prompt, auxInputPort):
        print(f"===== {prompt} =====")

        for port in input_pb2.AuxInputPort.keys():
            value = input_pb2.AuxInputPort.Value(port)
            print(f"{value}: {port}")

        selectedIndex = getInput("Enter the number of the port you want to select", int(auxInputPort))
        if input_pb2.AUX_INPUT_PORT_NORMAL <= selectedIndex <= input_pb2.AUX_INPUT_PORT_2:
            return selectedIndex
        else:
            print("Invalid selection. Returning default port.")
            return auxInputPort

    def selectSwitchType(self, prompt, switchType):
        print(f"===== {prompt} =====")

        for sType in device_pb2.SwitchType.keys():
            value = device_pb2.SwitchType.Value(sType)
            print(f"{value}: {sType}")

        selectedIndex = getInput("Enter the number of the switch type you want to select", int(switchType))
        if device_pb2.NORMALLY_OPEN <= selectedIndex <= device_pb2.NORMALLY_CLOSED:
            return selectedIndex
        else:
            print("Invalid selection. Returning default switch type.")
            return switchType

    def setAuxInput(self, auxInput):
        auxInput.acFail = self.selectAuxInputPort("Select Aux Input Port for AC Fail", auxInput.acFail)
        auxInput.typeAux0 = self.selectSwitchType("Select Switch Type for Aux Input 0", auxInput.typeAux0)
        auxInput.tamper = self.selectAuxInputPort("Select Aux Input Port for Tamper", auxInput.tamper)
        auxInput.typeAux1 = self.selectSwitchType("Select Switch Type for Aux Input 1", auxInput.typeAux1)
        auxInput.fire = self.selectAuxInputPort("Select Aux Input Port for Fire", auxInput.fire)
        auxInput.typeAux2 = self.selectSwitchType("Select Switch Type for Aux Input 2", auxInput.typeAux2)

    def selectResistanceValue(self, prompt, resistanceValue):
        print(f"===== {prompt} =====")

        for resValue in input_pb2.SupervisedResistanceValue.keys():
            value = input_pb2.SupervisedResistanceValue.Value(resValue)
            print(f"{value}: {resValue}")

        selectedIndex = getInput("Enter the number of the resistance value you want to select", int(resistanceValue))
        if input_pb2.SUPERVISED_REG_1K <= selectedIndex <= input_pb2.SUPERVISED_REG_CUSTOM:
            return selectedIndex
        else:
            print("Invalid selection. Returning default resistance value.")
            return resistanceValue

    def selectSupervisedInputRange(self, prompt, supervisedInputRange):
        print(f"===== {prompt} =====")

        supervisedInputRange.MinValue = getInput("Enter MinValue", supervisedInputRange.MinValue)
        supervisedInputRange.MaxValue = getInput("Enter MaxValue", supervisedInputRange.MaxValue)

    def selectSupervisedInputConfig(self, prompt, supervisedInputConfig):
        print(f"===== {prompt} =====")

        self.selectSupervisedInputRange("Select Short Range", supervisedInputConfig.short)
        self.selectSupervisedInputRange("Select Open Range", supervisedInputConfig.open)
        self.selectSupervisedInputRange("Select On Range", supervisedInputConfig.on)
        self.selectSupervisedInputRange("Select Off Range", supervisedInputConfig.off)

    def setSupervisedInput(self, sInput):
        sInput.portIndex = getInput("Enter PortIndex", sInput.portIndex)
        sInput.type = self.selectSwitchType("Select Switch Type", sInput.type)
        sInput.duration = getInput("Enter Duration", sInput.duration)
        sInput.resistance = self.selectResistanceValue("Select Resistance Value", sInput.resistance)
        self.selectSupervisedInputConfig("Select Supervised Input Config", sInput.config)

    def setInputConfig(self, deviceID):
        panelID = self.selectDeviceId("Enter Panel ID: ", deviceID, SlaveFilter.PANEL)
        if panelID == 0:
            print("Invalid Panel ID.")
            return

        inputConfig = self.inputSvc_.getConfig(panelID)
        if inputConfig is None:
            print("Failed to get input config.")
            return

        self.setAuxInput(inputConfig.auxInput)
        numOfSupervisedInput = getInput("Enter number of supervised inputs", len(inputConfig.supervisedInputs))
        for i in range(numOfSupervisedInput):
            self.setSupervisedInput(inputConfig.supervisedInputs[i])

        self.inputSvc_.setConfig(panelID, inputConfig)

        print("===== Set input config success =====")

    def getFacilityCodeConfig(self, deviceID):
        panelID = self.selectDeviceId("Enter Panel ID: ", deviceID, SlaveFilter.DI24)
        if panelID == 0:
            print("Invalid Panel ID.")
            return

        facilityCodeConfig = self.cardSvc_.getFacilityCodeConfig(panelID)
        if facilityCodeConfig is None:
            print("Failed to get facility code config.")
            return

        print("===== Facility code config =====")
        print(f"FacilityCodeConfig: {facilityCodeConfig}")

    def setFacilityCodeConfig(self, deviceID):
        panelID = self.selectDeviceId("Enter Panel ID: ", deviceID, SlaveFilter.DI24)
        if panelID == 0:
            print("Invalid Panel ID.")
            return

        facilityCodeConfig = self.cardSvc_.getFacilityCodeConfig(panelID)
        if facilityCodeConfig is None:
            print("Failed to get facility code config.")
            return
        
        if 0 < len(facilityCodeConfig.facilityCodes):
            del facilityCodeConfig.facilityCodes[:]

        for i in range(card_pb2.MAX_FACILITY_CODE):
            inputCode = getInput(f"Enter the Facility code[{i}]. Press Enter to stop...", -1)
            if inputCode == -1:
                break

            facilityCode = card_pb2.FacilityCode(code=f"{inputCode:04}".encode("utf-8"))
            facilityCodeConfig.facilityCodes.append(facilityCode)


        self.cardSvc_.setFacilityCodeConfig(panelID, facilityCodeConfig)
        print("===== Set facility code config success =====")

    def enrollUser(self, deviceID):
        uid = getInput("Please enter a userID: ", "1")
        if uid:
            userInfo = user_pb2.UserInfo(name=f"User_{uid}")

            userInfo.hdr.ID = uid
            userInfo.hdr.userFlag = user_pb2.USER_FLAG_CREATED

            userInfo.setting.securityLevel = user_pb2.SECURITY_LEVEL_NORMAL
            userInfo.setting.startTime = CS20485Test.TEST_USER_STARTTIME
            userInfo.setting.endTime = CS20485Test.TEST_USER_ENDTIME
            userInfo.setting.biometricAuthMode = auth_pb2.AUTH_MODE_NONE
            userInfo.setting.cardAuthMode = auth_pb2.AUTH_MODE_CARD_ONLY
            userInfo.setting.IDAuthMode = auth_pb2.AUTH_MODE_NONE

            print(f">> Select the card data you want to enroll...")
            scanDeviceID = self.selectDeviceId("Enter scan device ID: ", deviceID, SlaveFilter.SLAVE)
            if scanDeviceID == 0:
                print("Invalid Scan Device ID.")
                return

            cardData = self.cardSvc_.scan(scanDeviceID)
            if not cardData or not cardData.CSNCardData:
                print("Failed to scan card data")
                return

            userInfo.cards.append(cardData.CSNCardData)
            userInfo.hdr.numOfCard = 1

            self.userSvc_.enroll(deviceID, [userInfo], True)
            print(f"===== Enroll success {uid} =====")
