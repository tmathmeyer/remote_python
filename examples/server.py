
from pyremote import server

def main():
  s = server.Server()
  s.connect('192.168.0.102', 5006)
  s.wait()
