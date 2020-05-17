from typing import Optional, Dict

SERVER_PORT = 1973
SERVER_IP = '127.0.0.1'
SERVER_ADDR = SERVER_IP, SERVER_PORT

FIELD_SEP = '&'
NAME_VALUE_SEP = ':'


class Error(Exception):
    """ An error in the protocol """
    pass


class ChecksumError(Error):
    def __init__(self, actual_checksum, expected_checksum):
        super().__init__('Expected checksum of {} but got {}'
                         .format(actual_checksum, expected_checksum))


def is_exit_request_code(req_code: int):
    return req_code == 8


# def checksum_response(string: str) -> int:
#     return sum(map(ord, string))


# def checksum_request(request_code: int, request_data: str) -> None:
#     return checksum_response(request_data) + ord(str(request_code))


def checksum(**kwargs) -> int:
    return sum(sum(map(ord, name + str(value)))
               for name, value in kwargs.items())


def make_message_no_checksum(**kwargs) -> bytes:
    """ Create a message with some fields.
    Example: make_message(data1='hello', data2=2) will return
             'data1:hello&data2:2'
    :param kwargs: The fields.
    :return: The message in the format of the protocol.
    """
    fields = ('{}{}{}'.format(name, NAME_VALUE_SEP, value)
              for name, value in kwargs.items())

    return FIELD_SEP.join(fields).encode()


def make_message(**kwargs) -> bytes:
    kwargs['checksum'] = checksum(**kwargs)
    return make_message_no_checksum(**kwargs)


def parse_message(message: bytes) -> Optional[Dict[str, str]]:
    """
    :throws: Error
    """
    fields = message.decode().split(FIELD_SEP)

    #   Check for valid message fields
    if any(field for field in fields if NAME_VALUE_SEP not in field):
        raise Error('Incorrect message format')

    partitions = (field.partition(NAME_VALUE_SEP)
                  for field in fields)
    ret = {name: value for name, _, value in partitions}

    #   Check sum
    if 'checksum' in ret:
        no_checksum_dict = {name: value for name, value in ret.items()
                            if name != 'checksum'}
        my_checksum = int(checksum(**no_checksum_dict))
        his_checksum = int(ret['checksum'])
        if his_checksum != my_checksum:
            raise ChecksumError(my_checksum, his_checksum)

    return ret
