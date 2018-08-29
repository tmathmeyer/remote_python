
from . import netcmd_parse

class SimpleProxy(object):
  def __init__(self, connection, pool, deltype):
    self.connection = connection
    self.pool = pool
    self.deltype = deltype
  
  def write(self, msg):
    try:
      msg = str.encode(msg)
      self.connection.send( (len(msg)).to_bytes(4, byteorder='big') )
      self.connection.send(msg)
    except BrokenPipeError:
      del self.pool._objects[self.deltype]


  def make_call(self, instance_id, fn_name):
    def call(*args, **kwargs):
      action = netcmd_parse.Method(instance_id, fn_name, args, kwargs)
      self.write(netcmd_parse.ToJson(action))
    return call


class ObjectPool(object):
  def __init__(self):
    self._objects = {}

  def instantiate(self, inst, connection):
    inst.proxy = SimpleProxy(connection, self, inst.typeid)
    self._objects[inst.typeid] = inst

  def call(self, method):
    obj = self._objects.get(method.clazz, None)
    if obj is not None:
      getattr(obj, method.name)(*method.args, **method.kwargs)

  def query(self, query, connection):
    objects = [o for o in self._objects.values() if o.matches(query.typename, **query.kwargs)]
    action = netcmd_parse.Response(query.sender, objects)
    msg = str.encode(netcmd_parse.ToJson(action))
    connection.send( (len(msg)).to_bytes(4, byteorder='big') )
    connection.send(msg)

  def delete(self, delete):
    del self._objects[delete.objid]

  def apply(self, operation, connection):
    if type(operation) == netcmd_parse.Instantiate:
      self.instantiate(operation, connection)

    if type(operation) == netcmd_parse.Method:
      self.call(operation)

    if type(operation) == netcmd_parse.Query:
      self.query(operation, connection)

    if type(operation) == netcmd_parse.Delete:
      self.delete(operation)

