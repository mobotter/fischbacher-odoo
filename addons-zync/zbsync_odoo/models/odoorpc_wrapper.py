# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
class RPCWrapper(object):
    def __init__(self, connection, obj, ids):
        self.connection = connection
        self.obj = obj
        self.ids = ids

    def __str__(self):
        new_list = []
        for i in range(0, len(self.ids), 6):
            new_list.append(self.ids[i : i + 6])

        sids = "\n".join(map(str, new_list))
        return (
            f"{self.obj._name}@{self.connection}\n-----------------------------\n{sids}"
        )

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        ids = self.ids.__getitem__(item)
        if not isinstance(ids, list):
            ids = [ids]
        return RPCWrapper(self.connection, self.obj, ids)

    def clone(self, id):
        return RPCWrapper(self.connection, self.obj, [id])

    def _zbs_iterate_records(self, keep_small=False):
        for id in self.ids:
            obj = self.clone(id)
            if not keep_small:
                obj = obj.unwrap()
            yield obj

    def _zbs_unwrap(self):
        return self.unwrap()

    def unwrap(self):
        res = self.obj.browse(self.ids)
        setattr(res, "_zbs_connection", self.connection)
        res = res.with_context(_zbs_connection=self.connection)
        return res

    def _zebrooset_wrap(self):
        return self
