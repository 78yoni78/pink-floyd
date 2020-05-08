
from socket import socket, AF_INET, SOCK_STREAM
from helper import SERVER_ADDR, RequestCode, checksum_request

SERVER_PORT = 1973
SERVER_IP = '127.0.0.1'

REQUEST_CODE_NAMES = """1 - List all albums
2 - List album song
3 - Song length
4 - Song lyrics
5 - Song album
6 - Search song by name
7 - Search song by lyrics
8 - Quit """


def make_request(sock: socket, req_code: RequestCode, req_data: str) -> None:
    checksum = checksum_request(req_code, req_data)
    request = '{}&checksum:{}&data:{}'.format(req_code, checksum, req_data)
    sock.send(request.encode())


def main():
    with socket(AF_INET, SOCK_STREAM) as client_socket:

        print('Connecting to server... ', end='')
        client_socket.connect(SERVER_ADDR)
        data = client_socket.recv(1024).decode()
        print('connected!')
        print('')
        print(data)
        print(REQUEST_CODE_NAMES)
        while True:
            req_code = input('Choose an option: ')
            make_request(client_socket, req_code, 'shine')

            response = client_socket.recv(1024).decode()
            print(response)


if __name__ == '__main__':
    main()
