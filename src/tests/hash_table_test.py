import sys

sys.path.append("..")
from utils.hash_table import HashTable
from utils.block_signature_maker import BlockSignatureMaker


block_sizes = [8] #[4, 7, 10, 32, 64]
rolling_size = [12] #[7, 8, 8, 10, 11]


for i in range(len(block_sizes)):
    BLOCK_SIZE = block_sizes[i]
    rolling_size = rolling_size[i]
    M = 2**rolling_size

    hash_table = HashTable(rolling_size)

    with open("message.txt", "rb") as in_file:
        #block = bytearray(in_file.read(BLOCK_SIZE))
        block = in_file.read(BLOCK_SIZE)

        while block != b'':
            block_rolling_chechskum = BlockSignatureMaker.full_roling_checksum(block, BLOCK_SIZE, M)[0]
            block_md5 = BlockSignatureMaker.md5_hash(block)
            hash_table.add_value(block_rolling_chechskum, block_md5)
            block = in_file.read(BLOCK_SIZE)

    hash_table.print()
