import atexit
import uuid
import gc
import socket
import threading
import weakref

from . import netcmd_parse

remote_object_pool = {}
conn = None
thread = None
signal = True

def stopListening():
  signal = False
  for obj in remote_object_pool.values():
    proxy = obj()
    if proxy:
      proxy.delete()
  gc.collect()
  conn.close()
  thread.join()

atexit.register(stopListening)

class MetaLock(object):
  def __init__(self, lock):
    self.lock = lock
    self.data = None

  def acquire(self):
    self.lock.acquire()
    return self.data

  def release(self):
    self.lock.release()

def create_connection(ip, addr):
  global conn
  global thread
  conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  conn.connect((ip, addr))

  class SockReader(threading.Thread):
    def __init__(self):
      super(SockReader, self).__init__()
      self.locks = {}

    def run(self):
      while signal:
        data = conn.recv(int.from_bytes(conn.recv(4), byteorder='big'))
        if not signal:
          return
        action = netcmd_parse.FromJson(data.decode('utf-8'))
        if type(action) == netcmd_parse.Response:
          metalock = self.locks.get(action.sender, None)
          if metalock:
            del self.locks[action.sender]
            metalock.data = action.objects
            metalock.release()
          continue
        if type(action) == netcmd_parse.Method:
          obj = remote_object_pool.get(action.clazz, None)()
          if obj:
            getattr(obj, action.name)(*action.args, **action.kwargs)
          continue
        print(netcmd_parse.ToJson(action))

    def addResponseKey(self, sender):
      lock = MetaLock(threading.Lock())
      lock.acquire()
      self.locks[sender] = lock
      return lock

  thread = SockReader()
  thread.start()



def CreateRemoteObjectProxy(clazz):
  global conn
  global thread
  if conn is None:
    create_connection('127.0.0.1', 5005)

  def write(msg):
    if signal:
      msg = str.encode(msg)
      conn.send( (len(msg)).to_bytes(4, byteorder='big') )
      conn.send(msg)

  class __recorder__(object):
    def __init__(self, *args, **kwargs):
      clazz.query = lambda _, *args, **kwargs: self.query(*args, **kwargs)
      clazz.id = lambda _: self._id
      self._listeners = set()
      self._eventHandlers = {}
      self._id = str(uuid.uuid4())
      self._wrapped = clazz(*args, **kwargs)
      self._deleted = False
      remote_object_pool[self._id] = weakref.ref(self)
      remote_methods = ['acquireListener', 'removeListener', 'notify']
      object_ids = {}
      for method_name, method in clazz.__dict__.items():
        if getattr(method, '__remote_call__', None):
          remote_methods.append(method_name)
        if getattr(method, '__object_key__', None):
          object_ids[method_name] = getattr(self._wrapped, method_name)()
        if getattr(method, '__event_listener__', None):
          self._eventHandlers[method.__for_class__] = method
      action = netcmd_parse.Instantiate(clazz.__name__, self._id, remote_methods, object_ids)
      write(netcmd_parse.ToJson(action))

    def __getattr__(self, name):
      sentinal = object()
      method = getattr(self._wrapped, name, sentinal)
      if method is not sentinal and callable(method):
        name = method.__name__
        def result(*args, **kwargs):
          for listener in self._listeners:
            action = netcmd_parse.Method(listener, 'notify', [clazz.__name__, name, self._id], {})
            write(netcmd_parse.ToJson(action))
          method(*args, **kwargs)
        return result
      if name == 'notify':
        def notify(clazz, method=None, object_id=None):
          handler = self._eventHandlers.get(clazz, None)
          if handler:
            handler(self._wrapped, method, object_id)
        return notify
      raise AttributeError('{} not found'.format(name))

    def __del__(self):
      if self._deleted:
        return
      action = netcmd_parse.delete(self._id)
      write(netcmd_parse.tojson(action))

    def delete(self):
      self._deleted = True
      action = netcmd_parse.Delete(self._id)
      write(netcmd_parse.ToJson(action))

    def wait(self):
      thread.join()

    def acquireListener(self, listener_id):
      self._listeners.add(listener_id)

    def removeListener(self, listener_id):
      self._listeners.remove(listener_id)

    def query(self, clazz, **kwargs):
      action = netcmd_parse.Query(self._id, clazz, kwargs)
      write(netcmd_parse.ToJson(action))
      response = thread.addResponseKey(self._id)
      for o in response.acquire():
        o.proxy = self
        yield o
      response.release()

    def make_call(self, instance_id, fn_name):
      def call(*args, **kwargs):
        action = netcmd_parse.Method(instance_id, fn_name, args, kwargs)
        write(netcmd_parse.ToJson(action))
      return call

  return __recorder__


def Object(clazz):
  return CreateRemoteObjectProxy(clazz)


def Event(for_class):
  def decorator(func):
    func.__event_listener__ = True
    func.__for_class__ = for_class
    return func
  return decorator


def ObjectKey(func):
  func.__object_key__ = True
  return func


def RemoteCall(func):
  func.__remote_call__ = True
  return func
