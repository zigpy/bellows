class int_t(int):
    _signed = True

    def serialize(self):
        return self.to_bytes(self._size, 'little', signed=self._signed)

    @classmethod
    def deserialize(cls, data):
        r = cls.from_bytes(data[:cls._size], 'little', signed=cls._signed)
        data = data[cls._size:]
        return r, data


class int8s(int_t):
    _size = 1


class uint_t(int_t):
    _signed = False


class uint8_t(uint_t):
    _size = 1


class uint16_t(uint_t):
    _size = 2


class uint32_t(uint_t):
    _size = 4


class LVString(bytes):
    def serialize(self):
        return bytes([
            len(self),
        ]) + self

    @classmethod
    def deserialize(cls, data):
        l = int.from_bytes(data[:1], 'little')
        s = data[1:l + 1]
        return s, data[l + 1:]


def fixed_list(length, itemtype):
    class List(list):
        def serialize(self):
            assert len(self) == length
            return b''.join([i.serialize() for i in self])

        @classmethod
        def deserialize(cls, data):
            r = cls()
            for i in range(length):
                item, data = itemtype.deserialize(data)
                r.append(item)
            return r, data

    return List
