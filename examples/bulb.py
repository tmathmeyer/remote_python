from magicblue import MagicBlue  # Mock magic blue library
from pyremote import client

# Create connection to remote server
remote = client.Client('127.0.0.1', 5005)

@remote.shareClassspec
class Lightbulb(object):
  def __init__(self, bulb_mac, version):
    self._mac = bulb_mac
    self._bulb = MagicBlue(bulb_mac, version)
    self._mirror = None

  @remote.expose
  def TurnOn(self):
    self._bulb.turn_on()

  @remote.expose
  def TurnOff(self):
    self._bulb.turn_off()
    self._mirror = None

  @remote.expose
  def SetRGB(self, rgb):
    self._bulb.set_color(rgb)
    self._mirror.SetRGB(rgb)

  @remote.expose
  def ID(self):
    return self._mac

  @remote.expose
  def Manufacturer(self):
    return 'magicblue'

  def setMirrorBulb(self, bulb):
    self._mirror = bulb

if __name__ == '__main__':
  for mac, version in [('11:99', 10), ('22:88', 10), ('33:77', 10)]:
    bulb = Lightbulb(mac, version)
    remote.maintain_reference(bulb)
    if mac == '11:99':
      # This bulb changes color when the master bulb does,
      # but a restart breaks connection
      mirror = Lightbulb('44:66', 10)
      bulb.setMirrorBulb(mirror)
      remote.weak_reference(mirror)


