from pyremote import client


# Create connection to remote server
remote = client.Client('127.0.0.1', 5005)

Lightbulb = remote.getClassspec('Lightbulb')
Speaker = remote.getClassspec('Speaker')

class PanelController(object):
  def __init__(self):
    bulbs = {}
    speakers = {}

    for bulb in remote.getObjects(type=Lightbulb):
      bulb.listen_for_change(self)
      bulbs[bulb.ID()] = bulb

    for speaker in remote.getObjects(type=Speaker):
      speaker.listen_for_change(self)
      speakers[speaker.ID()] = speaker

  def changeSpeakerVolume(self, speaker_id, volume):
    speaker = speakers.get(speaker_id, None)
    if speaker:
      speaker.setVolume(volume)

  def getSpeakerVolume(self, speaker_id):
    speaker = speakers.get(speaker_id, None)
    if speaker:
      return speaker.getVolume()
    raise LookupError('speaker not found with ID = {}'.format(speaker_id))

