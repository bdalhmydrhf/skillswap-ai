import grpc
import logging
import time
import connect_pb2

from sampleMenu import MainMenuResourceType, SampleMenu
from sampleTest import SampleTest, getInput
from connectTest import ConnectTest

from example.master.master import MasterClient
from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.login.login import LoginSvc
from example.device.device import DeviceSvc
from example.face.face import FaceSvc
from example.card.card import CardSvc
from example.user.user import UserSvc
from example.operator.operator import OperatorSvc
from example.auth.auth import AuthSvc
from example.system.system import SystemSvc
from example.masteradmin.masteradmin import MasterAdminSvc
from example.event.event import EventSvc

class SampleMain:
    DEFAULTS = {
        "GATEWAY_CA_FILE": "c:/cert/gateway/ca.crt",
        "GATEWAY_ADDR": "192.168.43.108",
        "GATEWAY_PORT": 4000,
        "MASTER_CA_FILE": "c:/cert/master/master_ca.crt",
        "MASTER_ADDR": "192.168.43.108",
        "MASTER_PORT": 4010,
        "TENANT_CERT_FILE": "c:/cert/master/tenant_tenant1.crt",
        "TENANT_KEY_FILE": "c:/cert/master/tenant_tenant1_key.pem",
        "GATEWAY_ID": "gateway1",
        "MASTER_MODE": False,
    }
    SLEEP_TIME_DEVICE_READY = 5  # seconds

    def __init__(self):
        self.client_ = None
        self.channel_ = None
        self.connectSvc_ = None
        self.connTest_ = None
        self.progTest_ = None

    def setAllowConnectionFromDevice(self):
        while True:
            self.connTest_.showPendingList()
            allow = getInput("Check connected status (0: Check again, 1: Go test)", "0")
            if allow == "1":
                break

        self.connTest_.allowAll()

    def connectDevice(self, connInfo):
        if self.DEFAULTS["MASTER_MODE"]:
            return self.connectSvc_.connect(self.DEFAULTS["GATEWAY_ID"], connInfo)
        return self.connectSvc_.connect(connInfo)

    def disconnectAll(self):
        if self.DEFAULTS["MASTER_MODE"]:
            self.connectSvc_.disconnectAll(self.DEFAULTS["GATEWAY_ID"])
        else:
            self.connectSvc_.disconnectAll()

    def run(self):
        try:
            self.initializeGrpcClient()

            deviceSvc = DeviceSvc(self.channel_)
            faceSvc = FaceSvc(self.channel_)
            userSvc = UserSvc(self.channel_)
            operatorSvc = OperatorSvc(self.channel_)
            cardSvc = CardSvc(self.channel_)
            authSvc = AuthSvc(self.channel_)
            systemSvc = SystemSvc(self.channel_)
            masterAdminSvc = MasterAdminSvc(self.channel_)
            eventSvc = EventSvc(self.channel_)
            self.connTest_ = ConnectTest(self.connectSvc_)

            self.setAllowConnectionFromDevice()

            print(f"Waiting for {self.SLEEP_TIME_DEVICE_READY} seconds for the device to be ready...")
            time.sleep(self.SLEEP_TIME_DEVICE_READY)

            self.progTest_ = SampleTest(self.connTest_, self.connectSvc_, deviceSvc, userSvc, faceSvc, operatorSvc, cardSvc, authSvc, systemSvc, masterAdminSvc, eventSvc)
            self.progTest_.startDeviceEventListener()
            self.runTests()
        except Exception as e:
            print(f"Error during operation: {e}")
        finally:
            self.progTest_.stopDeviceEventListener()
            self.client_.close()

    def runTests(self):
        isExit = False
        while not isExit:
            selected = SampleMenu.showMenuMain()
            match selected:
                case MainMenuResourceType.EXIT:
                    isExit = True
                    self.progTest_.removeAllDevices()
                    self.progTest_.stopBackgroundTask()
                    self.progTest_.stopEventLogListener(1)
                case MainMenuResourceType.ADD_DEVICE:
                    self.progTest_.addDevice()
                case MainMenuResourceType.GET_DEVICE_LIST:
                    self.progTest_.getDeviceList()
                case MainMenuResourceType.REMOVE_DEVICE:
                    self.progTest_.removeDevice()
                case MainMenuResourceType.DEVICE_CAPABILITY:
                    self.progTest_.getDeviceCapability()
                case MainMenuResourceType.GET_ALL_USERS:
                    self.progTest_.getAllUsers()
                case MainMenuResourceType.ENROLL_USER:
                    self.progTest_.enrollUser()
                case MainMenuResourceType.ENROLL_USER_WITH_FACE:
                    self.progTest_.enrollUserWithFace()
                case MainMenuResourceType.DELETE_ALL_USERS:
                    self.progTest_.deleteAllUsers()
                case MainMenuResourceType.GET_AUTHCONFIG:
                    self.progTest_.getAuthConfig()
                case MainMenuResourceType.SET_AUTHCONFIG:
                    self.progTest_.setAuthConfig()
                case MainMenuResourceType.GET_OPERATOR:
                    self.progTest_.getOperator()
                case MainMenuResourceType.SET_OPERATOR:
                    self.progTest_.setOperator()
                case MainMenuResourceType.GET_SYSTEMCONFIG:
                    self.progTest_.getSystemConfig()
                case MainMenuResourceType.SET_SYSTEMCONFIG:
                    self.progTest_.setSystemConfig()
                case MainMenuResourceType.GET_MASTERADMIN:
                    self.progTest_.getMasterAdmin()
                case MainMenuResourceType.SET_MASTERADMIN:
                    self.progTest_.setMasterAdmin()
                case MainMenuResourceType.RESET_CONFIG:
                    self.progTest_.resetConfig()
                case MainMenuResourceType.FACTORY_RESET:
                    self.progTest_.factoryReset()
                case MainMenuResourceType.RUN_BG_TASK:
                    self.progTest_.runBackgroundTask()
                case MainMenuResourceType.STOP_BG_TASK:
                    self.progTest_.stopBackgroundTask()
                case MainMenuResourceType.START_MONITORING:
                    self.progTest_.startEventLogListener()
                case MainMenuResourceType.STOP_MONITORING:
                    self.progTest_.stopEventLogListener()
                case _:
                    print("Invalid selection.")

    def initializeGrpcClient(self):
        try:
            if self.DEFAULTS["MASTER_MODE"]:
                self.client_ = MasterClient(
                    getInput("Enter Master Address", self.DEFAULTS["MASTER_ADDR"]),
                    int(getInput("Enter Master Port", self.DEFAULTS["MASTER_PORT"])),
                    getInput("Enter Master CA File Path", self.DEFAULTS["MASTER_CA_FILE"]),
                    getInput("Enter Tenant Cert File Path", self.DEFAULTS["TENANT_CERT_FILE"]),
                    getInput("Enter Tenant Key File Path", self.DEFAULTS["TENANT_KEY_FILE"]),
                )
                self.channel_ = self.client_.getChannel()
                self.client_.setToken(LoginSvc(self.channel_).login(self.DEFAULTS["TENANT_CERT_FILE"]))
                self.connectSvc_ = ConnectMasterSvc(self.channel_)
            else:
                self.client_ = GatewayClient(
                    getInput("Enter Gateway Address", self.DEFAULTS["GATEWAY_ADDR"]),
                    int(getInput("Enter Gateway Port", self.DEFAULTS["GATEWAY_PORT"])),
                    getInput("Enter Gateway CA File Path", self.DEFAULTS["GATEWAY_CA_FILE"]),
                )
                self.channel_ = self.client_.getChannel()
                self.connectSvc_ = ConnectSvc(self.channel_)
        except Exception as e:
            print(f"Failed to initialize gRPC client: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig()
    app = SampleMain()
    app.run()