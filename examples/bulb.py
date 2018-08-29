
from magicblue import MagicBlue
import remote_object
import gc

@remote_object.Object
class Lightbulb(object):
  def __init__(self, bulb_mac, version):
    self._mac = bulb_mac
    self._bulb = MagicBlue(bulb_mac, version)

  @remote_object.RemoteCall
  def TurnOn(self):
    self._bulb.turn_on()

  @remote_object.RemoteCall
  def TurnOff(self):
    self._bulb.turn_off()

  @remote_object.RemoteCall
  def SetRGB(self, rgb):
    self._bulb.set_color(rgb)

  @remote_object.ObjectKey
  def ID(self):
    return self._mac

  @remote_object.ObjectKey
  def Manufacturer(self):
    return 'magicblue'

if __name__ == '__main__':
  bulbs = [Lightbulb(mac, version) for (mac, version) in [
    ('xx:xx:xx:xx:xx:xx', 10),
    ('xx:xx:xx:xx:xx:xx', 10),
    ('11:22:33:44:55:66', 10),
  ]]

  for bulb in bulbs:
    bulb.wait()
