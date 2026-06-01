from enum import Enum


class MainMenuResourceType(Enum):
    EXIT = 0
    GET_SLAVE_LIST = 1
    SEARCH_SLAVE = 2
    GET_INPUTCONFIG = 3
    SET_INPUTCONFIG = 4
    GET_FACILITYCODECONFIG = 5
    SET_FACILITYCODECONFIG = 6
    ENROLL_USER = 7

    @staticmethod
    def getDescription(value):
        return {
            MainMenuResourceType.EXIT: "Exit",
            MainMenuResourceType.GET_SLAVE_LIST: "Get slave list",
            MainMenuResourceType.SEARCH_SLAVE: "Search slave",
            MainMenuResourceType.GET_INPUTCONFIG: "Get InputConfig",
            MainMenuResourceType.SET_INPUTCONFIG: "Set InputConfig",
            MainMenuResourceType.GET_FACILITYCODECONFIG: "Get FacilityCodeConfig",
            MainMenuResourceType.SET_FACILITYCODECONFIG: "Set FacilityCodeConfig",
            MainMenuResourceType.ENROLL_USER: "Enroll user"
        }.get(value, str(value))


class CS20485Menu:
    @staticmethod
    def showMenuMain() -> MainMenuResourceType:
        print(">> Select menu...")
        print("--------------")
        for resource in MainMenuResourceType:
            print(f"{resource.value}: {MainMenuResourceType.getDescription(resource)}")
        print("--------------")

        while True:
            choice = input("Please select a number> ")
            if choice.isdigit() and int(choice) in [item.value for item in MainMenuResourceType]:
                return MainMenuResourceType(int(choice))
            print("Invalid input. Please try again.")
