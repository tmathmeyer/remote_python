

class MagicBlue(object):
  """Mock magic blue bulb"""

  def __init__(self, mac, version):
    pass

  def turn_off(self):
    print('turn off')

  def turn_on(self):
    print('turn on')

  def set_color(self, rgb):
    print('color = {}'.format(rgb))
