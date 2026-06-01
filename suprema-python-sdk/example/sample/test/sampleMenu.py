from enum import Enum


class MainMenuResourceType(Enum):
    EXIT = 0
    ADD_DEVICE = 1
    GET_DEVICE_LIST = 2
    REMOVE_DEVICE = 3
    DEVICE_CAPABILITY = 4
    GET_ALL_USERS = 5
    ENROLL_USER = 6
    ENROLL_USER_WITH_FACE = 7
    DELETE_ALL_USERS = 8
    GET_AUTHCONFIG = 9
    SET_AUTHCONFIG = 10
    GET_OPERATOR = 11
    SET_OPERATOR = 12
    GET_SYSTEMCONFIG = 13
    SET_SYSTEMCONFIG = 14
    GET_MASTERADMIN = 15
    SET_MASTERADMIN = 16
    RESET_CONFIG = 17
    FACTORY_RESET = 18
    RUN_BG_TASK = 19
    STOP_BG_TASK = 20
    START_MONITORING = 21
    STOP_MONITORING = 22

    @staticmethod
    def getDescription(value):
        return {
            MainMenuResourceType.EXIT: "Exit",
            MainMenuResourceType.ADD_DEVICE: "Add device",
            MainMenuResourceType.GET_DEVICE_LIST: "Get device list",
            MainMenuResourceType.REMOVE_DEVICE: "Remove device",
            MainMenuResourceType.DEVICE_CAPABILITY: "Get device capability",
            MainMenuResourceType.GET_ALL_USERS: "Get all users",
            MainMenuResourceType.ENROLL_USER: "Enroll a user",
            MainMenuResourceType.ENROLL_USER_WITH_FACE: "Enroll a user with face",
            MainMenuResourceType.DELETE_ALL_USERS: "Delete all users",
            MainMenuResourceType.GET_AUTHCONFIG: "Get auth config",
            MainMenuResourceType.SET_AUTHCONFIG: "Set auth config",
            MainMenuResourceType.GET_OPERATOR: "Get operators",
            MainMenuResourceType.SET_OPERATOR: "Set a operator",
            MainMenuResourceType.GET_SYSTEMCONFIG: "Get system config",
            MainMenuResourceType.SET_SYSTEMCONFIG: "Set system config",
            MainMenuResourceType.GET_MASTERADMIN: "Get master admin",
            MainMenuResourceType.SET_MASTERADMIN: "Set master admin",
            MainMenuResourceType.RESET_CONFIG: "Reset config",
            MainMenuResourceType.FACTORY_RESET: "Factory reset",
            MainMenuResourceType.RUN_BG_TASK: "Run background task",
            MainMenuResourceType.STOP_BG_TASK: "Stop background task",
            MainMenuResourceType.START_MONITORING: "Start monitoring",
            MainMenuResourceType.STOP_MONITORING: "Stop monitoring",
        }.get(value, str(value))


class SampleMenu:
    @staticmethod
    def showMenuMain() -> MainMenuResourceType:
        print(">> Select menu...")
        print("--------------")
        for resource in MainMenuResourceType:
            print(f"{resource.value}: {MainMenuResourceType.getDescription(resource)}")
        print("--------------")

        while True:
            choice = input("Please select a number> ")
            if choice == "":
                return MainMenuResourceType(0)
            if choice.isdigit() and int(choice) in [item.value for item in MainMenuResourceType]:
                return MainMenuResourceType(int(choice))
                print("Invalid input. Please try again.")
