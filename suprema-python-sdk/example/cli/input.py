class UserInput:
  text = ''
  defaultVal = ''

  def __init__(self, text, defaultVal):
    self.text = text
    self.defaultVal = defaultVal

  def getUserInput(userInputs):
    inputVals = []

    for userInput in userInputs:
      inputVal = input(f'>> {userInput.text}: ')
      if inputVal == '' and userInput.defaultVal != '':
        inputVals.append(userInput.defaultVal)
      else:
        inputVals.append(inputVal)

    return inputVals


  def getDeviceIDs():
    deviceIDs = []

    while True:
      devIDStr = input(f'Enter the device ID (Press just ENTER if no more device): ')

      if devIDStr.strip() == '':
        break

      try:
        devID = int(devIDStr)
        deviceIDs.append(devID)
      except ValueError as verr:
        print(f'Invalid device ID {devIDStr}: {verr}')
        break
    
    return deviceIDs

  @staticmethod
  def pressEnter(msg):
    input(f'{msg}')

  def getInteger(prompt, default=None, min=None, max=None):
    while True:
      try:
        if default is None:
          entered = input(f">> {prompt}: ")
        else:
          entered = input(f">> {prompt} (default: {default}): ")

        if not entered:
          if default is None:
            continue

          return default

        value = int(entered)

        if min is not None and value < min:
          print(f"min: {min}")
          continue
        if max is not None and value > max:
          print(f"max: {max}")
          continue
        
        return value
      except ValueError as e:
        continue

  def getIntegers(prompt, default=None, min=None, max=None):
    while True:
      try:
        if default is None:
          entered = input(f">> {prompt}: ")
        else:
          entered = input(f">> {prompt} (default: {default}): ")

        if not entered:
          if default is None:
            continue

          return default

        values = [int(x) for x in entered.split()]

        for value in values:
          if min is not None and value < min:
            print(f"min: {min}")
            continue
          if max is not None and value > max:
            print(f"max: {max}")
            continue

        return values
      except ValueError as e:
        continue

  def getBoolean(prompt, default=False):
    while True:
      if default:
        entered = input(f">> {prompt}? [1*: Yes 0: No]: ")
      else:
        entered = input(f">> {prompt}? [1: Yes 0*: No]: ")

      if not entered:
        return default
      
      if entered == "1":
        return True
      elif entered == "0":
        return False

  def getBytes(prompt, default):
    length = len(default)

    while True:
      try:
        entered = input(f">> {prompt} (length: {length}, default: {default.hex(' ')}): ")

        if entered == "":
          return default

        value = bytes.fromhex(entered)

        if len(value) != length:
          print(f"length: {len(value)}/{length}")
          continue

        return value
      except ValueError as e:
        continue

  def getStrings(prompt, default=None):
    while True:
      entered = input(f">> {prompt} (default: {default}): ")

      if entered == "":
        return default

      return entered.split()