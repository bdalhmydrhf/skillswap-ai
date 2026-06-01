from enum import Enum
from example.cli.input import UserInput


class MainMenuResourceType(Enum):
  EXIT = 0
  UPDATE_FACECONFIG_TEMPLATEONLY = 1
  GET_USER = 2
  REMOVE_USER = 3
  ENROLL_USER = 4

def showMenuMain(default=MainMenuResourceType.EXIT, prompt="Select menu..."):
  print("--------------\n")
  msg = f"""{prompt}
    {MainMenuResourceType.EXIT.value}: Exit
    {MainMenuResourceType.UPDATE_FACECONFIG_TEMPLATEONLY.value}: Update face config (template only)
    {MainMenuResourceType.GET_USER.value}: Get user
    {MainMenuResourceType.REMOVE_USER.value}: Remove user
    {MainMenuResourceType.ENROLL_USER.value}: Enroll user
  Please select a number> """

  return UserInput.getInteger(msg, default.value)

class FaceMenuResourceType(Enum):
  SCAN_FACE = 1
  WITH_IMAGE = 2
  WITH_TEMPLATE = 3

def showMenuFace(default=FaceMenuResourceType.SCAN_FACE, prompt="Where do you get face data from?"):
  print("--------------\n")
  msg = f"""{prompt}
    {FaceMenuResourceType.SCAN_FACE.value}: From Device (Scan)
    {FaceMenuResourceType.WITH_IMAGE.value}: From Image (Enroll with image)
    {FaceMenuResourceType.WITH_TEMPLATE.value}: From Image (Enroll template only)
  Please select a number> """

  return UserInput.getInteger(msg, default.value)
