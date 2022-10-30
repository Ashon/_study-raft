import transport.messages as messages


_STORE = {}


# COMMANDS = {
#     # log commands
#     'set': (store.set_value, 2),
#     'get': (store.get_value, 1)
# }


def get_value(key):
    value = _STORE.get(key)

    if not value:
        return messages.CMD_DATAEMPTY

    return f'{messages.CMD_OK} {value}'


def set_value(key, value):
    global _STORE

    _STORE[key] = value

    return messages.CMD_OK


def del_value(key):
    global _STORE

    del _STORE[key]

    return messages.CMD_OK
