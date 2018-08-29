#!/usr/bin/env python

import socket
import threading
import netcmd_parse
import object_pool


class ServerSignal(object):
  def __init__(self, finished=False):
    self.finished = finished
  def complete(self):
    self.finished = True


class ConnectionDataListener(threading.Thread):
  def __init__(self, conn, addr, buffer_size, func, pool):
    super(ConnectionDataListener, self).__init__()
    self._conn = conn
    self._addr = addr
    self._func = func
    self._signal = ServerSignal()
    self._pool = pool

  def run(self):
    while not self._signal.finished:
      data = self._conn.recv(int.from_bytes(self._conn.recv(4), byteorder='big'))
      if not data:
        self._signal.complete()
        break
      self._func(data.decode('utf-8'), self._addr, self._conn, self._pool)

  def finish(self):
    self._signal.complete()


NEVER = ServerSignal()
def OnSocketData(ip, port, buffer_size, signal=NEVER):
  pool = object_pool.ObjectPool()
  def decorate(func):
    def create_server(*args, **kwargs):
      if args or kwargs:
        print('{} cant be called with arguments')
        return
      _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      _socket.bind((ip, port))
      _socket.listen(1)
      threads = []
      while not signal.finished:
        conn, addr = _socket.accept();
        cdl = ConnectionDataListener(conn, addr, buffer_size, func, pool)
        threads.append(cdl)
        cdl.start()
      for cdl in threads:
        cdl.finish()
        cdl.join()
    return create_server
  return decorate


KILL_ = ServerSignal()


@OnSocketData('127.0.0.1', 5005, 256, KILL_)
def ObjectPoolServer(data, addr, conn, pool):
  action = netcmd_parse.FromJson(str(data))
  pool.apply(action, conn)
  print((addr, action))


if __name__ == '__main__':
  ObjectPoolServer()
