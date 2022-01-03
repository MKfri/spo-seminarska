import sys

sys.path.append("..")
from utils.block_signature_maker import BlockSignatureMaker



# To je test pravilne implementacije izračuna checksuma
# Preverjamo ali se "rolling checksum" ujema s tistim iz celotnega zaporedja bytov

block_sizes = [4, 7, 10, 32, 64]
modulos = [128, 256, 256, 1024, 2048]

match_count = 0
fail_count = 0

with open("message.txt", "rb") as in_file:
	block = bytearray(in_file.read())

	data_len = len(block)

	for i in range(len(block_sizes)):
		BLOCK_SIZE = block_sizes[i]
		M = modulos[i]

		bsm = BlockSignatureMaker(BLOCK_SIZE, M)

		start = 0
		end = BLOCK_SIZE
		while (end < data_len):
			rolling = 0
			if start == 0:
				bsm.add_whole_block(block[start: end])
				rolling = bsm.get_rolling_checksum()
			else:
				for k in range(BLOCK_SIZE):
					current_byte = block[start + k]
					bsm.append_byte(current_byte)
					rolling = bsm.get_rolling_checksum()

			with_offset = BlockSignatureMaker.full_roling_checksum(block[start: end], BLOCK_SIZE, M)
			#print(rolling)
			#print(with_offset[0])
			#print("Match?", rolling == with_offset[0])

			if rolling == with_offset[0]:
				match_count += 1
			else:
				fail_count += 1

			start = end
			end += BLOCK_SIZE

print(f"Summary: Match {match_count}; Fail {fail_count}")
