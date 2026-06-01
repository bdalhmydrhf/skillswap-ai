from enum import Enum


class MainMenuResourceType(Enum):
    EXIT = 0
    RUN_ACTION = 1

    @staticmethod
    def getDescription(value):
        return {
            MainMenuResourceType.EXIT: "Exit",
            MainMenuResourceType.RUN_ACTION: "Run action"
        }.get(value, str(value))


class RunActionMenu:
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
