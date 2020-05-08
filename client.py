from socket import socket, AF_INET, SOCK_STREAM
import helper
from helper import RequestCode

EXIT_REQUEST_CODE = 8

REQUEST_CODE_NAMES = """1 - List all albums
2 - List album song
3 - Song length
4 - Song lyrics
5 - Song album
6 - Search song by name
7 - Search song by lyrics
8 - Quit """


def get_request(sock: socket, req_code: RequestCode, req_data: str) -> str:
    checksum = helper.checksum_request(req_code, req_data)
    request = '{}&checksum:{}&data:{}'.format(req_code, checksum, req_data)
    return request


def get_response(sock: socket) -> str:
    response = sock.recv(1025).decode()
    checksum_field, data_field = response.split('&')
    checksum = checksum_field[len('checksum:'):]
    resp_data = data_field[len('data:'):]

    if checksum != helper.checksum_response(resp_data):
        raise Exception('Invalid checksum')

    return resp_data


def main():
    with socket(AF_INET, SOCK_STREAM) as sock:

        print('Connecting to server... ', end='')
        sock.connect(helper.SERVER_ADDR)
        welcome_msg = sock.recv(1024).decode()
        print('connected! \n')
        print(welcome_msg)

        stay_connected = True
        while stay_connected:
            print(REQUEST_CODE_NAMES)
            req_code = input('Choose an option: ')
            sock.send(get_request(sock, req_code, 'shine').encode())

            response = sock.recv(1024).decode()
            print(response)

            if int(req_code) == EXIT_REQUEST_CODE:
                stay_connected = False


if __name__ == '__main__':
    main()
