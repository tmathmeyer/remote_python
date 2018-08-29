import remote_object

@remote_object.Object
class LightPanel(object):
  def __init__(self):
    for bulb in self.query('Lightbulb', Manufacturer='magicblue'):
      bulb.acquireListener(self)

  def change_bulb_color(self, bulb_id, rgb):
    for bulb in self.query('Lightbulb', ID=bulb_id):
      bulb.SetRGB(rgb)

  @remote_object.Event('Lightbulb')
  def on_bulb_change(self, method, object_id):
    print(method)


if __name__ == '__main__':
  panel = LightPanel()
  panel.change_bulb_color('11:22:33:44:55:66', [233, 41, 42])
  panel.wait()





