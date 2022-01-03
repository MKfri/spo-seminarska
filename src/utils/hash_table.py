

class HashTable:
    
    def __init__(self, checksum_bit_size):
        # Poracunamo na nacin kompatibilen z lihimi velikosti checksuma
        if checksum_bit_size % 2 == 1:
            checksum_bit_size += 1

        self.hash_bit_size = int(checksum_bit_size / 2)
        self.modulo = 2**self.hash_bit_size
        self.index_size = 2**self.hash_bit_size
        self.index_array = [[] for k in range(self.index_size)]


    def compute_hash(self, key):
        # Vzamemo spodnjo polovico bitov in prišetjemo zgornjo polovico
        ostanek = key % self.modulo
        kolicnik = key // self.modulo
        hashed_value = (ostanek + kolicnik) % self.index_size
        #print("Hash:", hashed_value)
        return hashed_value

    def get_values(self, rolling_checksum):
        hash = self.compute_hash(rolling_checksum)
        # Vrnemo list tuplov
        return self.index_array[hash]

    def get_md5s(self, rolling_checksum):
        md5s = []
        for (rolling, md5) in self.get_values(rolling_checksum):
            if rolling == rolling_checksum:
                md5s.append(md5)
        return md5s

    def add_value(self, rolling_checksum, block_md5_hash):
        hash = self.compute_hash(rolling_checksum)
        #print(hash)
        self.index_array[hash].append((rolling_checksum, block_md5_hash))

    def print(self):
        print(f"index_size: {self.index_size}; modulo: {self.modulo}; hash_bit_size: {self.hash_bit_size}")
        for i in range(self.index_size):
            print(f"[{i}] => {self.index_array[i]}")
