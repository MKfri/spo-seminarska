

class ArgParser:
    default_port = 20220
    default_block_size = 100
    default_rolling_size = 32

    program_name = ""

    def __init__(self, args):
        self.args = args
        
        self.port = 0
        self.block_size = 0
        self.rolling_size = 0
        self.file_name = ""
        self.success = True
        
        self.parse()

    def parse(self):
        self.program_name = self.args[0]
        
        if len(self.args) == 1:
            self.success = False
        else:
            self.file_name = self.args[1]
            for arg in self.args[2:]:
                self.parse_switch(arg)

    def parse_switch(self, argument):
        value = argument[3:]
        int_val = int(value)
        
        if argument.startswith("-p="):
            self.port = int_val
        elif argument.startswith("-b="):
            self.block_size = int_val
        elif argument.startswith("-r="):
            self.rolling_size = int_val
        else:
            self.success = False

    def get_port(self):
        if self.port == 0:
            return ArgParser.default_port
        return self.port

    def get_block_size(self):
        if self.block_size == 0:
            return ArgParser.default_block_size
        return self.block_size

    def get_rolling_size(self):
        if self.rolling_size == 0:
            return ArgParser.default_rolling_size
        return self.rolling_size
    
    def get_file_name(self):
        return self.file_name

    def get_sanitized_file_name(self):
        splitted = self.file_name.split("/")
        sanitized = splitted[-1]
        splitted = sanitized.split("\\")
        return splitted[-1]



    def print_help(self):
        print("Uporaba:")
        print(f"python {self.program_name} <ime-datoteke>")
        print()
        print("Opcijski parametri:")
        print("-p=<port>")
        print("-b=<block-size>")
        print("-r=<size-of-rolling-checksum>")


    
