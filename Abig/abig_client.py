import socket
from string import ascii_lowercase
SERVER_IP = '127.0.0.1'# socket.gethostname()
SERVER_PORT = 1973
PASSWORD = 'Pink Floyd'
ALBUMS_LIST = '1'
SONGS_LIST_IN_ALBUM = '2'
SONGS_LENGTH = '3'
SONGS_LYRICS = '4'
SONGS_ALBUM = '5'
WORD_IN_SONGS_NAMES = '6'
WORD_IN_SONGS_LYRICS = '7'
EXIT = '8'
CHECKSUM_ERROR = '-1'

def password_check():
    """
    : checks if the user knows the password (Pink Floyd)
    : True if the user knows and false if he doesnt
    """
    users_try = input("befor we will give you access to the server,\nwhats is the password?")
    if users_try == PASSWORD:
        return True
    else:
        return False

def print_menu():
    """
    : prints the options menu to the user
    """
    print("\noptions list:");
    print("--------------");
    print("1- get Pink Floyds albums list");
    print("2- get all the songs names in certain album");
    print("3- get certain songs length");
    print("4- get certain songs lyrics");
    print("5- find songs album");
    print("6- finds songs that has a certain word in thier name");
    print("7- finds songs that has a certain word in thier lyrics");
    print("8- exit\n")

def check_choice(choice :int):
    """
    : checks if the choice is valid
    : output: True if the choice is valid and false if it isnt
    """
    return (choice <= int(EXIT) and choice >= int(ALBUMS_LIST))

def creats_messege(choice :str):
    """
    : asks for data if needed and unifies a messeg to the server
    : output: the messege as string
    """
    if (choice == ALBUMS_LIST):
        data = ''
    elif(choice == SONGS_LIST_IN_ALBUM):
        data = input("enter albums name: ")
    elif(choice == SONGS_LENGTH):
        data = input("enter the name of the song: ")
    elif(choice == SONGS_LYRICS):
        data = input("enter the name of the song: ")
    elif(choice == SONGS_ALBUM):
        data = input("enter the songs name: ")
    elif(choice == WORD_IN_SONGS_NAMES):
        data = input("enter word you would like to look for: ")
    elif(choice == WORD_IN_SONGS_LYRICS):
        data = input("enter word you would like to find in lyrics: ")
    else:
        data = "problem..." #debug
    checksum_part1 = sum(map(ord, data))
    checksum_part2 = ord(choice)
    total_checksum = str(checksum_part1 + checksum_part2)
    if total_checksum == '':
        total_checksum = '0'
    msg_to_server = "{0}&checksum:{1}&data:{2}".format(choice, total_checksum, data)

    return msg_to_server
 
def checksumCalc(data :str):
    """
    : the function calculates the checksum for the data (suming ascii values)
    : output: the checksum as int
    """
    data = data.lower()
    letters_values = {c: i for i, c in enumerate(ascii_lowercase, 1)} # creats dict of ascii values
    checksum = sum(letters_values.get(c, 0) for c in data if c) # calculates according to the dict

    return sum(map(ord, data))

def print_server_response(server_msg):
    """
    : prints the servers answer.Also reports if there is a problem with the servers check sum.
    : output: none
    """
    server_msg_list = server_msg.split("&")
    checksum = server_msg_list[0].replace("checksum:", "")
    data = server_msg_list[1].replace("data:", "")
    if check_with_checksum(checksum, data):
        print(data)
    else:
        print("there was a problem with the servers checksum...\n")
    
	
	
def check_with_checksum(checksum :str, data:str):
    """
    : check if the checksum is okay.
    : output: True if the checksum is OK and false otherways
    """
    actual_checksum = checksumCalc(data)
    if actual_checksum != int(checksum):

        return False
    else:

        return True
    
 
def main():
    password = password_check()
    while (password != True):
        print("its not the password!\n")
        password = password_check()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (SERVER_IP, SERVER_PORT)
    sock.connect(server_address)
    server_msg = sock.recv(1024)
    server_msg = server_msg.decode()
    server_msg_list = server_msg.split("&")
    data = server_msg_list[1].replace("data:", "")
    print(data)
	
    print_menu()
    choice = int(input("enter your choice: "))
    while not(check_choice(choice)):
        print("invalid choice value.\n")
        choice = int(input("enter your choice: "))

    while str(choice) != EXIT:
        msg = creats_messege(str(choice))
        sock.sendall(msg.encode())
	
        server_msg = sock.recv(1024)
        server_msg = server_msg.decode()
        print_server_response(server_msg)

        print_menu()
        choice = int(input("enter your choice: "))
        while not(check_choice(choice)):
            print("invalid choice value.\n")
            choice = int(input("enter your choice: "))

    checksum = ord(EXIT)
    msg = "{1}&checksum:{0}&data:".format(checksum, EXIT)
    sock.sendall(msg.encode())
    
	
	
	
if __name__ == "__main__":
    main()
