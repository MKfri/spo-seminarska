import hashlib
import base64


class BlockSignatureMaker:

	def __init__(self, block_size, modulo):
		self.block_size = block_size
		self.modulo = modulo


	def add_whole_block(self, block):
		# Za initial_block se pricakuje bytearray
		self.current_block = block
		checksums = BlockSignatureMaker.full_roling_checksum(block, self.block_size, self.modulo)
		self.rolling_checksum = checksums[0]
		self.a_checksum = checksums[1]
		self.b_checksum = checksums[2]


	def full_roling_checksum(block, block_size, M):
		# block => array of bytes (values between 0 and 255)
		a_checksum = sum(block)

		b_checksum = 0
		for i in range(len(block)):
			b_checksum += block[i]*(block_size-i)

		# Modulo je potenca stevila 2, recimo 2**m
		# sledece operacije se v optimizirani verziji algoritma izvajajo kot hitre bitne operacije:
		# % => AND z ustrezno masko s prizganimi zadnjimi m biti
		# M * b_checksum + a_checksum => SHIFT LEFT in OR
		a_checksum = a_checksum % M
		b_checksum = b_checksum % M

		rolling_checksum = M * b_checksum + a_checksum

		return (rolling_checksum, a_checksum, b_checksum)


	def md5_hash(block):
		# Python ima vgrajeno podporo za MD5 zgoscevalno funkcijo
		# Input: byte list
		# Output: ascii reprezentacija MD5
		md5_byte_val = hashlib.md5(block).digest()
		return base64.b64encode(md5_byte_val).decode("ascii")


	def append_byte(self, next_byte):
		outgoing_byte = self.current_block.pop(0)
		self.current_block.append(next_byte)

		# Uporabimo rekurencni formuli za ucinkovit izracun
		self.a_checksum = (self.a_checksum - outgoing_byte + next_byte) % self.modulo
		self.b_checksum = (self.b_checksum - self.block_size*outgoing_byte + self.a_checksum) % self.modulo

		self.rolling_checksum = self.modulo * self.b_checksum + self.a_checksum

		return outgoing_byte


	def get_rolling_checksum(self):
		return self.rolling_checksum


	def get_md5(self):
		return BlockSignatureMaker.md5_hash(self.current_block)


	# Funkciji za posiljanje preostalih bytov ko pridemo do konca datoteke
	# for k in range(get_byte_number()):
	#   if (checksum matches):
	#       sporoci ujemanje & koncaj
	#   else:
	#       send(flush_first_byte())
	def get_byte_number(self):
		return len(self.current_block)

	def flush_first_byte(self):
		outgoing_byte = self.current_block.pop(0)

		self.a_checksum = (self.a_checksum - outgoing_byte) % self.modulo
		self.b_checksum = (self.b_checksum - self.block_size*outgoing_byte + self.a_checksum) % self.modulo
		
		self.rolling_checksum = self.modulo * self.b_checksum + self.a_checksum

		return outgoing_byte
