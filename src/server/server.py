
import sys
import os
import socket
import json

sys.path.append("..")
from utils.hash_table import HashTable
from utils.block_signature_maker import BlockSignatureMaker


SUCCESS = bytes("success", "ascii")

PORT = 20220
HOST = socket.gethostname()


cli_args = sys.argv

if len(cli_args) > 2:
    print("Opcijsko lahko podas le port:")
    print(f"python {cli_args[0]} -p=<port>")
    exit(1)
elif len(cli_args) == 2:
    PORT = int(cli_args[1][3:])



# Ustvarimo socket
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind socket
try:
    soc.bind((HOST, PORT))
except socket.error as message:
    print(f"Error: binding to port {PORT}")
    print(f"Message: {message}")
    exit(1)

# Nastavimo velikost vrste za zahtevke
soc.listen(1024)

# Sprejmemo enega odjemalca
clientSocket, addr = soc.accept()
print(f"Got a connection from {addr}")



def send_message(string_to_send):
    # Poslji
    clientSocket.send(bytes(string_to_send, "ascii"))
    # In pocakaj potrditev
    response = clientSocket.recv(1024)
    if response != SUCCESS:
        print("Response: ", response.decode("ascii"))
        print("Exiting")
        clientSocket.close()
        soc.close()
        exit(1)
    


initial_message = clientSocket.recv(1024)
initial_message_str = initial_message.decode("ascii")
initial_message_json = json.loads(initial_message_str)
#print(initial_message_str)

FILE_NAME = initial_message_json["file_name"]
BLOCK_SIZE = initial_message_json["block_size"]
ROLLING_SIZE = initial_message_json["rolling_size"]
m_exponent = int(ROLLING_SIZE / 2)
M = 2**m_exponent


clientSocket.send(SUCCESS)


hash_table = HashTable(ROLLING_SIZE)

final_msg_received = False
block_count = 0

while not final_msg_received:
    block_message = clientSocket.recv(1024)
    block_message_str = block_message.decode("ascii")
    block_message_json = json.loads(block_message_str)

    message_type = block_message_json["type"]

    if message_type == "block":
        block_rolling_chechskum = block_message_json["rolling"]
        # MD5 v obliki ascii niza
        block_md5 = block_message_json["md5"]
        hash_table.add_value(block_rolling_chechskum, block_md5)

    elif message_type == "final":
        final_msg_received = True
        block_count = block_message_json["block_count"]
    
    else:
        print(f"Error unexpected message type {message_type}")
        clientSocket.close()
        soc.close()
        exit(1)

    clientSocket.send(SUCCESS)

    

# Pridobili smo vse podatke in jih shranili v hash table
#hash_table.print()



# Za posiljanje dolzine datoteke
file_len = {
    "type": "info",
    "status": "success",
    "file_size": 0
}

# Odpremo zahtevano datoteko
input_file = None
try:
    input_file = open(FILE_NAME, "rb")
    # Prestavimo se na konec datoteke
    input_file.seek(0, os.SEEK_END)
    # In preberemo stevilo predhodnih bytov
    file_len["file_size"] = input_file.tell()
    input_file.seek(0)
except IOError:
    print(f"Error opening file {FILE_NAME}")
    file_len["status"] = "fail"


# Posljemo dolzino datoteke v bytih
file_len_str = json.dumps(file_len)
send_message(file_len_str)

if file_len["status"] != "success":
    print("Exiting")
    exit(1)



# Zacenmo z iskanjem ujemanj
offset = 0
bsm = BlockSignatureMaker(BLOCK_SIZE, M)

rolling_checksum_computed_count = 0
rolling_checksum_match_count = 0
md5_match_count = 0

block_match = {
    "type": "match",
    "md5": "",
    "offset": 0
}
byte_to_send = {
    "type": "data",
    "value": 0,
    "offset": 0
}

flushed_block = True
read_size = BLOCK_SIZE

while True:
    data = bytearray(input_file.read(read_size))
    if len(data) == 0:
        break

    if flushed_block:
        # 0 < len(data) <= BLOCK_SIZE
        flushed_block = False
        bsm.add_whole_block(data)
        read_size = 1
    else:
        # len(data) == 1
        # Posljemo byte, ki ni del nobenega podvojenega bloka
        outgoing_byte = bsm.append_byte(data[0])
        byte_to_send["value"] = outgoing_byte
        byte_to_send["offset"] = offset
        byte_to_send_str = json.dumps(byte_to_send)
        
        send_message(byte_to_send_str)
        
        offset += 1
        #print("sending one byte: ", chr(outgoing_byte), "Offset=", offset)
    
    # Preverimo ce je trenutni blok podvojen
    rolling_checksum = bsm.get_rolling_checksum()
    md5s = hash_table.get_md5s(rolling_checksum)

    rolling_checksum_computed_count += 1
    
    if len(md5s) > 0:
        this_block_md5 = bsm.get_md5()
        if this_block_md5 in md5s:
            flushed_block = True
            read_size = BLOCK_SIZE
            # Sporocimo ujemanje
            block_match["md5"] = this_block_md5
            block_match["offset"] = offset
            block_match_str = json.dumps(block_match)

            # Posljemo md5 hash ujemajocega bloka in njegov offset
            send_message(block_match_str)
            
            #print("Block at offset matches: ", offset)
            #print(bsm.current_block)

            offset += bsm.get_byte_number()

            md5_match_count += 1
        rolling_checksum_match_count += 1


# Ko pridemo do koncamo moramo poslati se vse vrednosti skrite v BlockSignatureMaker-ju
if not flushed_block:
    length = bsm.get_byte_number()
    for k in range(length):
        outgoing_byte = bsm.flush_first_byte()

        # Posiljamo byte
        byte_to_send["value"] = outgoing_byte
        byte_to_send["offset"] = offset
        byte_to_send_str = json.dumps(byte_to_send)
        send_message(byte_to_send_str)
        offset += 1

        # Ce je se kaj bytov ostalo poskusimo sreco z ujemanjem
        if bsm.get_byte_number() > 0:
            rolling_checksum = bsm.get_rolling_checksum()
            md5s = hash_table.get_md5s(rolling_checksum)

            rolling_checksum_computed_count += 1
            
            if len(md5s) > 0:
                rolling_checksum_match_count += 1
                this_block_md5 = bsm.get_md5()
                if this_block_md5 in md5s:
                    # Preostanek bloka se ujema, sporocimo ujemanje in koncamo
                    block_match["md5"] = this_block_md5
                    block_match["offset"] = offset
                    block_match_str = json.dumps(block_match)
                    send_message(block_match_str)
                    
                    md5_match_count += 1
                    break



# Konec
final_message = {
    "type": "final"
}
final_message_str = json.dumps(final_message)
send_message(final_message_str)



print("Povzetek:")
print(f"Stevilo izracunov rolling checksum: {rolling_checksum_computed_count}")
print(f"Stevilo ujemanj rolling checksum: {rolling_checksum_match_count}")
print(f"Stevilo ujemanj md5: {md5_match_count}")
print(f"Stevilo laznih ujemanj: {rolling_checksum_match_count - md5_match_count}")


input_file.close()
clientSocket.close()
soc.close()
