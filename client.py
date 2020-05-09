from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from typing import Tuple

import helper
from helper import RequestCode

REQUEST_CODE_NAMES = """1 - List all albums
2 - List album song
3 - Length of song
4 - Lyrics of song
5 - Get album of song
6 - Search song by name
7 - Search song by lyrics
8 - Quit """

#   Missing requests codes do not hold data
REQUEST_CODE_PROMPTS = {
    2: 'Choose an album: ',
    3: 'Choose a song: ',
    4: 'Choose a song: ',
    5: 'Choose a song: ',
    6: 'Choose a word to search: ',
    7: 'Choose a a word to search: ',
}


def get_request(sock: socket, req_code: RequestCode, req_data: str) -> str:
    checksum = helper.checksum_request(req_code, req_data)
    request = '{}&checksum:{}&data:{}'.format(req_code, checksum, req_data)
    return request


def get_response(sock: socket) -> str:
    response = sock.recv(1025).decode()
    checksum_field, data_field = response.split('&')
    checksum = checksum_field[len('checksum:'):]
    resp_data = data_field[len('data:'):]

    if int(checksum) != helper.checksum_response(resp_data):
        raise Exception('Invalid checksum')

    return resp_data


def connect_to_server() -> Tuple[socket, str]:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(helper.SERVER_ADDR)

    welcome_msg = sock.recv(1024).decode()

    return sock, welcome_msg


def main():
    print('Connecting to server...', end='')
    sock, welcome_msg = connect_to_server()
    with sock:
        print('connected! \n')
        print(welcome_msg)

        stay_connected = True
        while stay_connected:
            print(REQUEST_CODE_NAMES)
            req_code = int(input('Choose an option: '))

            #   If the request code requires data, ask for it
            data = ''
            if req_code in REQUEST_CODE_PROMPTS:
                data = input(REQUEST_CODE_PROMPTS[int(req_code)])

            request = get_request(sock, req_code, data)

            try:
                sock.send(request.encode())

                response = get_response(sock)
                print(response)
            except SocketError as e:
                print('Oops! It seams you were disconnected. '
                      'Try again or check your internet connection. '
                      '\n{}'.format(e))
                stay_connected = False

            if helper.is_exit_request_code(req_code):
                stay_connected = False


if __name__ == '__main__':
    main()
