#   import data
from socket import socket, AF_INET, SOCK_STREAM
from typing import Tuple
import helper
from helper import RequestCode

DEFAULT_RESPONSES = {
    1: 'List albums',
    2: 'List album song',
    3: 'Song length',
    4: 'Song lyrics',
    5: 'Song album',
    6: 'Search song by name',
    7: 'Search song by lyrics',
    8: 'Quit',
}

EXIT_REQUEST_CODE = 8

WELCOME = 'Welcome to the pink floyd server!'


def get_request_fields(request: str) -> Tuple[RequestCode, str]:
    request_code, checksum_field, data_field = request.split('&')

    request_checksum = int(checksum_field[len('checksum:'):])
    request_data = data_field[len('data:'):]
    helper.checksum_request(request_code, request_data)

    if request_checksum != helper.checksum_request(request_code, request_data):
        raise Exception('Invalid Checksum')

    return request_code, request_data


def get_response(request_code: RequestCode,
                 request_data: str) -> None:
    resp_data = DEFAULT_RESPONSES[int(request_code)]
    checksum = helper.checksum_response(resp_data)
    response = 'checksum:{}&data:{}'.format(checksum, resp_data)

    return response


def get_listen_socket() -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(helper.SERVER_ADDR)
    sock.listen(1)
    return sock


def main():
    with get_listen_socket() as listen_sock:
        print('Server listening')

        while True:
            client_sock, client_addr = listen_sock.accept()
            with client_sock:
                print('Connected to {}'.format(client_addr))
                client_sock.send(WELCOME.encode())

                stay_connected = True
                while stay_connected:
                    request = client_sock.recv(1024).decode()
                    print('Client: {}'.format(request))

                    req_code, req_data = get_request_fields(request)
                    print('{} {}'.format(req_code, req_data))
                    response = get_response(req_code, req_data)

                    print('Server: {}'.format(response))
                    client_sock.send(response.encode())

                    if int(req_code) == EXIT_REQUEST_CODE:
                        stay_connected = False


if __name__ == '__main__':
    main()
