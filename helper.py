from typing import Union

RequestCode = Union[int, str]

SERVER_PORT = 1973
SERVER_IP = '127.0.0.1'
SERVER_ADDR = SERVER_IP, SERVER_PORT


def checksum_response(string: str) -> int:
    return sum(map(ord, string))


def checksum_request(request_code: RequestCode, request_data: str) -> None:
    return checksum_response(request_data) + ord(str(request_code))

