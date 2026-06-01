import enum
import grpc
import threading
import time
import datetime
from datetime import timezone
import connect_pb2
import device_pb2
import user_pb2
import auth_pb2
import face_pb2
from typing import List, Optional


def printFields(pb_obj):
    from google.protobuf.descriptor import FieldDescriptor

    print(f"--- {pb_obj.__class__.__name__} ---", flush=True)
    for field in pb_obj.DESCRIPTOR.fields:
        value = getattr(pb_obj, field.name)

        if field.type == FieldDescriptor.TYPE_ENUM:
            enum_name = field.enum_type.values_by_number.get(value)
            if enum_name:
                value = f"{enum_name.name} ({value})"
        
        print(f"{field.name}: {value}", flush=True)

def getInput(prompt, default):
    userInput = input(f"{prompt} (default: {default}): ") or default
    if userInput == "":
        return default
    try:
        return type(default)(userInput)
    except ValueError:
        print(f"Invalid input.", flush=True)
        return default
    
def getBoolean(prompt, default):
    userInput = input(f"{prompt} (y/n, default: {'y' if default else 'n'}): ").strip().lower()
    if userInput == "":
        return default
    if userInput in ['y', 'yes']:
        return True
    elif userInput in ['n', 'no']:
        return False
    else:
        return default

def getBoolInput(prompt, default) -> int:
    userInput = input(f"{prompt} (y/n, default: {'y' if default != 0 else 'n'}): ").strip().lower()
    if userInput == "":
        return 1 if default != 0 else 0
    if userInput in ['y', 'yes']:
        return 1
    elif userInput in ['n', 'no']:
        return 0
    else:
        return 1 if default != 0 else 0

def getDevices(prompt) -> List[int]:
    deviceIDsInput = input(f"{prompt}: ")
    deviceIDs = []
    for idStr in deviceIDsInput.split(","):
        try:
            deviceID = int(idStr.strip())
            if deviceID > 0:
                deviceIDs.append(deviceID)
        except ValueError:
            print(f"Invalid device ID: {idStr}. Skipping.", flush=True)
    return deviceIDs

def getTypeName(type):
    try:
        return device_pb2.Type.Name(type)
    except ValueError as e:
        return device_pb2.Type.Name(device_pb2.UNKNOWN)

def selectCameraFrequency(prompt, default):
    print(f"===== {prompt} =====", flush=True)
    print("0: Auto", flush=True)
    print("1: 50Hz", flush=True)
    print("2: 60Hz", flush=True)

    while True:
        selectedIndex = getInput("Select camera frequency", default)
        if selectedIndex in [0, 1, 2]:
            return selectedIndex
        else:
            print("Invalid selection. Please try again.", flush=True)

def selectCardOperationMask(prompt, default):
    print(f"===== {prompt} =====", flush=True)
    print(f"0x00000800: CUSTOM_DESFIRE_EV1", flush=True)
    print(f"0x00000400: CUSTOM_CLASSIC_PLUS", flush=True)
    print(f"0x00000200: BLE", flush=True)
    print(f"0x00000100: NFC", flush=True)
    print(f"0x00000080: SEOS", flush=True)
    print(f"0x00000040: SR_SE", flush=True)
    print(f"0x00000020: DESFIRE_EV1", flush=True)
    print(f"0x00000010: CLASSIC_PLUS", flush=True)
    print(f"0x00000008: ICLASS", flush=True)
    print(f"0x00000004: MIFARE_FELICA", flush=True)
    print(f"0x00000002: HIDPROX", flush=True)
    print(f"0x00000001: EM", flush=True)

    while True:
        selectedIndex = getInput("Enter card operation mask (hex)", default)
        if 0 <= selectedIndex <= 0x8FFFFFFF:
            return selectedIndex | 0x80000000
        else:
            print("Invalid selection. Please try again.", flush=True)


class SlaveFilter(enum.Enum):
    ALL = 0
    PANEL = 1
    DI24 = 2
    SLAVE = 3


class SampleTest:
    QUEUE_SIZE = 16
    DEFAULT_DEVICE_IPADDR = "192.168.40.114"
    DEFAULT_DEVICE_PORT = 51211
    TEST_USER_STARTTIME = 946684800
    TEST_USER_ENDTIME = 1924991999
    SLEEP_TIME_THREAD = 10
    CODE_MAP_FILE = "c:/cert/event_code.json"
    FIRST_DOOR_EVENT = 0x5000
    LAST_DOOR_EVENT = 0x5E00

    def __init__(self, connTest, connectSvc, deviceSvc, userSvc, faceSvc, operatorSvc, cardSvc, authSvc, systemSvc, masterAdminSvc, eventSvc):
        self.connTest_ = connTest
        self.connectSvc_ = connectSvc
        self.deviceSvc_ = deviceSvc
        self.userSvc_ = userSvc
        self.faceSvc_ = faceSvc
        self.operatorSvc_ = operatorSvc
        self.cardSvc_ = cardSvc
        self.authSvc_ = authSvc
        self.systemSvc_ = systemSvc
        self.masterAdminSvc_ = masterAdminSvc
        self.eventSvc_ = eventSvc
        self.eventCh_ = None
        self.eventThread_ = None
        self.eventStopEvent_ = threading.Event()
        self.statusCh_ = None
        self.statusStopEvent_ = threading.Event()
        self.statusThread_ = None
        self.selectedID_ = 0
        self.worker_ = None
        self.stopFlag_ = False

        self.eventSvc_.initCodeMap(SampleTest.CODE_MAP_FILE)


    def getStatusString(self, statusCh):
        try:
            for status in statusCh:
                if self.statusStopEvent_.is_set():
                    print('Status listener stopping...', flush=True)
                    break

                if status.status == connect_pb2.TCP_CONNECTED:
                    print(f"Device {status.deviceID} Connected (TCP)", flush=True)
                    self.startEventLogListener(status.deviceID)
                if status.status == connect_pb2.TLS_CONNECTED:
                    print(f"Device {status.deviceID} Connected (TLS)", flush=True)
                    self.startEventLogListener(status.deviceID)
                if status.status == connect_pb2.TCP_CANNOT_CONNECT:
                    print(f"Device {status.deviceID} Cannot connect (TCP)", flush=True)
                if status.status == connect_pb2.TLS_CANNOT_CONNECT:
                    print(f"Device {status.deviceID} Cannot connect (TLS)", flush=True)
                if status.status == connect_pb2.TCP_NOT_ALLOWED:
                    print(f"Device {status.deviceID} Not allowed (TCP)", flush=True)
                if status.status == connect_pb2.TLS_NOT_ALLOWED:
                    print(f"Device {status.deviceID} Not allowed (TLS)", flush=True)
                if status.status == connect_pb2.DISCONNECTED:
                    print(f"Device {status.deviceID} Disconnected", flush=True)
                    self.stopEventLogListener(status.deviceID)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                print('Subscription is cancelled', flush=True)
            else:
                print(f'Cannot get the device status: {e}', flush=True)

    def startDeviceEventListener(self):
        if self.statusThread_ is None or not self.statusThread_.is_alive():
            self.statusCh_ = self.connectSvc_.subscribe(self.QUEUE_SIZE)
            self.statusStopEvent_.clear()
            self.statusThread_ = threading.Thread(target=self.getStatusString, args=(self.statusCh_,))
            self.statusThread_.start()

    def stopDeviceEventListener(self):
        if self.statusThread_ and self.statusThread_.is_alive():
            if self.statusCh_:
                self.statusCh_.cancel()
                self.statusCh_ = None

            self.statusStopEvent_.set()
            self.statusThread_.join()
            self.statusThread_ = None

    def addDevice(self):
        print()
        print(f"===== Add Device =====", flush=True)

        ipAddr = getInput("IP Address", self.DEFAULT_DEVICE_IPADDR)
        port = getInput("Port", self.DEFAULT_DEVICE_PORT)
        useSSL = getBoolean("Use SSL", False)

        result = self.connTest_.connect(ipAddr, port, useSSL)
        print(f"{ipAddr}:{port} - {result}", flush=True)

    def getDeviceList(self):
        deviceIDs = self.connTest_.getConnectedDevice()
        if len(deviceIDs) == 0:
            print("No connected devices.", flush=True)
            return
        
        print(f"===== Connected Devices =====", flush=True)
        for id in deviceIDs:
            try:
                print(f"- {id}", flush=True)
                deviceInfo = self.deviceSvc_.getInfo(id)
                if deviceInfo:
                    print(f"{deviceInfo}")
            except grpc.RpcError as e:
                print(f"Cannot get device info for device {id}: {e}", flush=True)
                return

    def removeDevice(self):
        deviceIDs = self.connTest_.getConnectedDevice()
        if len(deviceIDs) == 0:
            print("No connected devices.", flush=True)
            return
        
        print(f"===== Connected Devices =====", flush=True)
        for id in deviceIDs:
            print(f"- {id}")

        selectedDevices = getDevices("Select device IDs to remove (comma separated, or press Enter to cancel): ")
        if len(selectedDevices) == 0:
            print("No devices selected. Canceling removal.", flush=True)
            return
        
        for id in selectedDevices:
            try:
                self.connectSvc_.disconnect([id])
                print(f"Device {id} removed successfully.", flush=True)
            except grpc.RpcError as e:
                print(f"Cannot remove device {id}: {e}", flush=True)
                return

    def removeAllDevices(self):
        try:
            self.connectSvc_.disconnectAll()
            print("All devices removed successfully.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot remove all devices: {e}", flush=True)
            return

    def selectDeviceID(self) -> int:
        deviceIDs = self.connTest_.getConnectedDevice()
        if len(deviceIDs) == 0:
            return 0
        
        print(f"Select device ID")
        while True:
            for id in deviceIDs:
                print(f"- {id}", flush=True)

            inputID = getInput(f"Enter device ID", self.selectedID_)
            if inputID == 0:
                return 0
            
            if inputID in deviceIDs:
                self.selectedID_ = inputID
                return inputID
            else:
                print(f"Invalid device ID: {inputID}. Please select from the list.", flush=True)

    def getDeviceCapability(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return
        
        try:
            capability = self.deviceSvc_.getCapability(deviceID)
            if capability:
                printFields(capability)
            else:
                print("No capability information available.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot get device capability: {e}", flush=True)
            return
        
    def deleteAllUsers(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            if getBoolean(f"Delete all users from device {deviceID}", True):
                self.userSvc_.deleteAll(deviceID)
                print(f"All users deleted successfully from device {deviceID}.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot delete all users: {e}", flush=True)
            return

    def getAllUsers(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return
        
        try:
            userInfos = self.userSvc_.getList(deviceID)
            print(f"===== Users on Device {deviceID} =====", flush=True)
            for userInfo in userInfos:
                print(f"{userInfo}")
        except grpc.RpcError as e:
            print(f"Cannot get all users: {e}", flush=True)
            return

    def enrollUser(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            uid = getInput(f"Please enter a userID for enroll", "1")
            if 0 < len(uid):
                hdr = user_pb2.UserHdr(ID=uid, userFlag=user_pb2.USER_FLAG_CREATED)
                setting = user_pb2.UserSetting(startTime=SampleTest.TEST_USER_STARTTIME,
                                            endTime=SampleTest.TEST_USER_ENDTIME,
                                            securityLevel=user_pb2.SECURITY_LEVEL_NORMAL,
                                            biometricAuthMode=auth_pb2.AUTH_MODE_NONE,
                                            cardAuthMode=auth_pb2.AUTH_MODE_CARD_ONLY,
                                            IDAuthMode=auth_pb2.AUTH_MODE_NONE)
                userInfo = user_pb2.UserInfo(hdr=hdr, setting=setting, name=f"User_{uid}")

                # print(f"Please scan a card to enroll...", flush=True)
                # cardData = self.cardSvc_.scan(deviceID)
                # if cardData and cardData.CSNCardData:
                #     userInfo.cards.append(cardData.CSNCardData)
                #     userInfo.hdr.numOfCard = 1

                self.userSvc_.enroll(deviceID, [userInfo], True)
                print(f"===== Enroll success {uid} =====", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot enroll user: {e}", flush=True)
            return

    def enrollUserWithFace(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            uid = getInput(f"Please enter a userID for enroll", "1")
            if 0 < len(uid):
                hdr = user_pb2.UserHdr(ID=uid, userFlag=user_pb2.USER_FLAG_CREATED)
                setting = user_pb2.UserSetting(startTime=SampleTest.TEST_USER_STARTTIME,
                                            endTime=SampleTest.TEST_USER_ENDTIME,
                                            securityLevel=user_pb2.SECURITY_LEVEL_NORMAL,
                                            biometricAuthMode=auth_pb2.AUTH_MODE_NONE,
                                            cardAuthMode=auth_pb2.AUTH_MODE_CARD_ONLY,
                                            IDAuthMode=auth_pb2.AUTH_MODE_NONE)
                userInfo = user_pb2.UserInfo(hdr=hdr, setting=setting, name=f"User_{uid}")

                print(f"Please look at the camera to capture face data...", flush=True)
                faceData = []
                face = self.faceSvc_.scan(deviceID, face_pb2.BS2_FACE_ENROLL_THRESHOLD_DEFAULT)
                faceData.append(face)
                userInfo.faces.extend(faceData)
                userInfo.hdr.numOfFace = 1

                self.userSvc_.enroll(deviceID, [userInfo], True)
                print(f"===== Enroll success {uid} =====", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot enroll user: {e}", flush=True)
            return

    def getAuthConfig(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            config = self.authSvc_.getConfig(deviceID)
            if config:
                printFields(config)
            else:
                print("No auth config available.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot get auth config: {e}", flush=True)
            return

    def setAuthConfig(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            config = self.authSvc_.getConfig(deviceID)
            if config is None:
                print("No auth config available.", flush=True)
                return

            users = self.userSvc_.getList(deviceID)
            if len(users) == 0:
                print("No users available to set auth config.", flush=True)
                return

            while True:
                operatorID = getInput("Enter Operator ID to set auth config", "0")
                if operatorID == "0":
                    print("Cancel setting auth config.", flush=True)
                    break

                config.operators.append(auth_pb2.Operator(userID=operatorID, level=auth_pb2.OPERATOR_LEVEL_CONFIG))

            self.authSvc_.setConfig(deviceID, config)
            print(f"Auth config set successfully for device {deviceID}.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot set auth config: {e}", flush=True)
            return


    def getOperator(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return
        
        try:
            operators = self.operatorSvc_.getList(deviceID)
            print(f"===== Operators on Device {deviceID} =====", flush=True)
            for operator in operators:
                print(f"{operator}")

        except grpc.RpcError as e:
            print(f"Cannot get operators: {e}", flush=True)
            return

    def setOperator(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected", flush=True)
            return

        try:
            uid = getInput(f"Please enter a userID for set operator", "1")
            oper = auth_pb2.Operator(userID=uid, level=auth_pb2.OPERATOR_LEVEL_CONFIG)
            self.operatorSvc_.add(deviceID, [oper])
            print(f"===== Set operator success {uid} =====", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot set operator: {e}", flush=True)
            return

    def getSystemConfig(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            config = self.systemSvc_.getConfig(deviceID)
            if config:
                printFields(config)
            else:
                print("No system config available.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot get system config: {e}", flush=True)
            return

    def setSystemConfig(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return
        
        try:
            config = self.systemSvc_.getConfig(deviceID)
            if config is None:
                print("No system config available.", flush=True)
                return
            
            print(f"Current system config: {config}", flush=True)

            config.timeZone = getInput("Enter timezone", config.timeZone)
            config.syncTime = getBoolean("Enable time sync", config.syncTime)
            config.isLocked = getBoolean("Is device locked", config.isLocked)
            config.useInterphone = getBoolean("Enable interphone", config.useInterphone)
            config.OSDPKeyEncrypted = getBoolean("Enable OSDP secure key", config.OSDPKeyEncrypted)
            config.useJobCode = getBoolean("Enable job code", config.useJobCode)
            config.useAlphanumericID = getBoolean("Enable alphanumeric ID", config.useAlphanumericID)
            config.cameraFrequency = selectCameraFrequency("Select camera frequency", config.cameraFrequency)
            config.useSecureTamper = getBoolean("Enable secure tamper", config.useSecureTamper)
            config.useCardOperationMask = selectCardOperationMask("Select card operation mask", config.useCardOperationMask)
            config.adminTwoStepAuth = getBoolean("Enable admin two-step authentication", config.adminTwoStepAuth)

            self.systemSvc_.setConfig(deviceID, config)
        except grpc.RpcError as e:
            print(f"Cannot set system config: {e}", flush=True)
            return

    def getMasterAdmin(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return
        
        try:
            masterAdmin = self.masterAdminSvc_.get(deviceID)
            if masterAdmin:
                printFields(masterAdmin)
            else:
                print("No master admin information available.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot get master admin: {e}", flush=True)
            return

    def setMasterAdmin(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            masterAdmin = user_pb2.UserInfo(hdr=user_pb2.UserHdr(ID="0"))

            pin = getInput("Enter master admin PIN", "123456")
            if 0 < len(pin):
                masterAdmin.PIN = self.userSvc_.hashPIN(pin)

            numOfFace = getInput("Enter the number of Faces", 0)
            faceData = []
            for i in range(numOfFace):
                print(f">> Select the face image file to extract the template.", flush=True)
                warpedData = self.getFaceImage(deviceID)
                if not warpedData:
                    print(f'Normalize failed from image.', flush=True)
                    continue

                templateData = self.getTemplateData(deviceID, warpedData)
                if not templateData:
                    print(f'Extract failed from image.', flush=True)
                    continue

                face = face_pb2.FaceData(index=i, flag=face_pb2.BS2_FACE_FLAG_EX|face_pb2.BS2_FACE_FLAG_TEMPLATE_ONLY, templates=[templateData])
                faceData.append(face)

            masterAdmin.faces.extend(faceData)
            masterAdmin.hdr.numOfFace = len(faceData)

            self.masterAdminSvc_.set(deviceID, masterAdmin)
            print(f"Set master admin successfully.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot set master admin: {e}", flush=True)
            return

    def resetConfig(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            if getBoolean("Reset device configuration. Do you want to continue?", True):
                self.deviceSvc_.resetConfig(deviceID, True)
                print(f"Device {deviceID} configuration reset successfully.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot reset device configuration: {e}", flush=True)
            return

    def factoryReset(self):
        deviceID = self.selectDeviceID()
        if deviceID == 0:
            print("No device selected.", flush=True)
            return

        try:
            if getBoolean("Factory reset device. Do you want to continue?", True):
                self.deviceSvc_.resetDevice(deviceID)
                print(f"Device {deviceID} factory reset successfully.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot factory reset device: {e}", flush=True)
            return

    def getFaceImage(self, deviceID) -> Optional[bytes]:
        try:
            path = getInput("Enter the image file path", "c:/mypic.jpg")
            if path:
                with open(path, 'rb') as f:
                    unwarpedData = f.read()
                    warpedData = self.faceSvc_.normalize(deviceID, unwarpedData)
                    if not warpedData:
                        print(f"Cannot normalize the image: {deviceID}", flush=True)
                        return None

                    return warpedData
        except grpc.RpcError as e:
            print(f"Cannot get the face image: {e}", flush=True)
            return None
        except FileNotFoundError as e:
            print(f"Cannot find the file: {path}", flush=True)
            return None
        except IOError as e:
            print(f"Cannot read the file: {path}", flush=True)
            return None
        finally:
            f.close()

        return None

    def getTemplateData(self, deviceID, warpedData) -> Optional[bytes]:
        try:
            templateData = self.faceSvc_.extract(deviceID, warpedData, True)
            if not templateData:
                print(f"Cannot extract the template data.", flush=True)
                return None

            return templateData
        except grpc.RpcError as e:
            print(f"Cannot extract the template data: {e}", flush=True)
            return None

    def runBackgroundTask(self):
        print("Running background task...", flush=True)

        def background_task():
            while not self.stopFlag_:
                time.sleep(SampleTest.SLEEP_TIME_THREAD)
                self.getDeviceList()

        self.worker_ = threading.Thread(target=background_task)
        self.worker_.start()

    def stopBackgroundTask(self):
        self.stopFlag_ = True
        if self.worker_:
            self.worker_.join()
            self.worker_ = None
            print("Background task stopped.", flush=True)

    def onLogReceived(self):
        try:
            if self.eventCh_ is not None:
                for event in self.eventCh_:
                    if self.eventStopEvent_.is_set():
                        break

                    match event.eventCode:
                        case code if code >= SampleTest.FIRST_DOOR_EVENT and code <= SampleTest.LAST_DOOR_EVENT:
                            print(f"{datetime.datetime.fromtimestamp(event.timestamp, timezone.utc)}: Door {event.entityID}, {self.eventSvc_.getEventString(event.eventCode, event.subCode)}", flush=True)
                        case _:
                            print(f"{datetime.datetime.fromtimestamp(event.timestamp, timezone.utc)}: Device {event.deviceID}, User {event.userID}, {self.eventSvc_.getEventString(event.eventCode, event.subCode)}", flush=True)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                print('Event subscription is cancelled', flush=True)
            else:
                print(f'Cannot get the event log: {e}', flush=True)

    def startEventLogListener(self, deviceID = 0):
        try:
            if deviceID == 0:
                deviceID = self.selectDeviceID()
                if deviceID == 0:
                    print("No device selected.", flush=True)
                    return
                print(f"Start event log listener manually for device {deviceID}.", flush=True)
            else:
                print(f"Start event log listener for device {deviceID}.", flush=True)

            self.eventSvc_.disableMonitoring(deviceID)
            self.eventSvc_.enableMonitoring(deviceID)

            self.eventCh_ = self.eventSvc_.subscribe(SampleTest.QUEUE_SIZE)
            eventThread = threading.Thread(target=self.onLogReceived)
            eventThread.start()

        except grpc.RpcError as e:
            print(f"Cannot start event log listener: {e}", flush=True)

    def stopEventLogListener(self, deviceID = 0):
        try:
            if deviceID == 0:
                deviceID = self.selectDeviceID()
                if deviceID == 0:
                    print("No device selected.", flush=True)
                    return
                print(f"Stop event log listener manually for device {deviceID}.", flush=True)
            elif deviceID == 1:
                print(f"Stop event log listener.", flush=True)
                return
            else:
                print(f"Stop event log listener for device {deviceID}.", flush=True)

            self.eventSvc_.disableMonitoring(deviceID)
            if self.eventCh_ is not None:
                self.eventCh_.cancel()
            self.eventCh_ = None
            print("Event log listener stopped.", flush=True)
        except grpc.RpcError as e:
            print(f"Cannot stop event log listener: {e}", flush=True)
