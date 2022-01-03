
import sys
import socket
import json
import base64

sys.path.append("..")
from utils.block_signature_maker import BlockSignatureMaker
from utils.arg_parser import ArgParser


# Parse CLI parameters
arg_parser = ArgParser(sys.argv)
if not arg_parser.success:
    arg_parser.print_help()
    exit(1)

BLOCK_SIZE = arg_parser.get_block_size()
ROLLING_SIZE = arg_parser.get_rolling_size()
m_exponent = int(ROLLING_SIZE / 2)
M = 2**m_exponent

FILE_NAME = arg_parser.get_file_name()
SANITIZED_FILE_NAME = arg_parser.get_sanitized_file_name()


PORT = arg_parser.get_port()
HOST = socket.gethostname()

SUCCESS = bytes("success", "ascii")



input_file = None

try:
    input_file = open(FILE_NAME, "rb")
except IOError:
    print(f"Error opening file {FILE_NAME}")
    exit(1)


# Ustvarimo in se povezemo na socket
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    soc.connect((HOST, PORT))
except socket.error as message:
    print(f"Error binding to port {PORT}")
    print(f"Message: {message}")
    input_file.close()
    exit(1)


def send_message(string_to_send):
    # Poslji
    soc.send(bytes(string_to_send, "ascii"))
    # In pocakaj potrditev
    response = soc.recv(1024)
    if response != SUCCESS:
        print("Response: ", response.decode("ascii"))
        print("Exiting")
        exit(1)



initial_message = {
    "type": "initial",
    "file_name": SANITIZED_FILE_NAME,
    "block_size": BLOCK_SIZE,
    "rolling_size": ROLLING_SIZE
}

initial_message_str = json.dumps(initial_message)
#print(initial_message_str)

# Odjemalcu posljemo sporocilo za zacetek sinhronizacije
send_message(initial_message_str)


# Zacnemo posiljati bloke
block = input_file.read(BLOCK_SIZE)
block_count = 0


# Tu bloke shranimo za kasnejso izgradnjo nove datoteke.
# Ker se ne omejujemo s porabo pomnilnika hranimo kar celotne bloke.
# Sicer bi lahko hranili le offsete od zacetka datoteke ter bi jih
# ob izgradnji ponovno prebrali in zapisali na ustrezno mesto.
# Predpostavki: 
# - datoteke NE gradimo in place, ampak naredimo tmp file in ko koncamo prepisemo original
# - ucinkovit random access do datoteke, da je dostop do bloka na offsetu hiter
block_store = {}

while block != b'':
    block_count += 1

    block_rolling_chechskum = BlockSignatureMaker.full_roling_checksum(block, BLOCK_SIZE, M)[0]
    block_md5 = BlockSignatureMaker.md5_hash(block)

    # Shranimo za kasneje
    block_store[block_md5] = block

    block_message = {
        "type": "block",
        "rolling": block_rolling_chechskum,
        "md5": block_md5 #base64.b64encode(block_md5).decode("ascii")
    }
    block_message_str = json.dumps(block_message)
    # Send message
    send_message(block_message_str)

    #print(block_message_str)

    # Preberemo nov blok in ponovimo vse skupaj
    block = input_file.read(BLOCK_SIZE)


# Here we are done with reading
# Later we will write to temporary file and overwrite this one
input_file.close()


# Posljemo se sporocilo o stevilu blokov
final_message = {
    "type": "final",
    "block_count": block_count
}
final_message_str = json.dumps(final_message)
send_message(final_message_str)

#print(final_message_str)


# Zacnemo poslusati za sporocila
# Prvo bo velikost datoteke, ki hkrati sporoca uspesem prevzem blokov
size_response = soc.recv(1024)
size_response_str = size_response.decode("ascii")
size_response_json = json.loads(size_response_str)

file_size = 0
reconstructed_file = None #bytearray()

if size_response_json["status"] != "success":
    print(f"Action failed, response: {size_response_json} ")
    print("Exiting")
    exit(1)
else:
    file_size = size_response_json["file_size"]
    reconstructed_file = bytearray(file_size)
    #print("file_size =", file_size)
    soc.send(SUCCESS)


blocks_matched = 0
single_bytes_transfered = 0

final_msg_received = False

while not final_msg_received:
    message = soc.recv(1024)
    message_str = message.decode("ascii")
    message_json = json.loads(message_str)

    message_type = message_json["type"]

    if message_type == "match":
        offset = message_json["offset"]
        md5 = message_json["md5"]
        
        block = block_store[md5]
        block_len = len(block)

        # Prekopiramo blok
        #print(block)
        reconstructed_file[offset:offset+block_len] = block
        blocks_matched += 1

    elif message_type == "data":
        offset = message_json["offset"]
        value = message_json["value"]
        # Popravimo samo en byte
        #print(f"{offset} => {value} [{chr(value)}]")
        reconstructed_file[offset] = value
        single_bytes_transfered += 1

    elif message_type == "final":
        final_msg_received = True
    else:
        print("Error, message_type does not match")
        print(message_str)
        exit(1)

    soc.send(SUCCESS)

# Decode as ascii and print
# print(reconstructed_file.decode("ascii"))

# Datoteko shranimo na disk na mesto stare
with open(SANITIZED_FILE_NAME, "wb") as output_file:
    output_file.write(reconstructed_file)



print("Povzetek:")
print(f"Zacetno stevilo blokov: {block_count}")

print(f"Ujemanj blokov: {blocks_matched}")
print(f"Stevilo prejetih posameznih byteov: {single_bytes_transfered}")

soc.close()
