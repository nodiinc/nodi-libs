import sys
sys.path.append('/root/edge')
from pymodbus.datastore import (ModbusSequentialDataBlock,
                                ModbusServerContext,
                                ModbusSlaveContext,
                                ModbusSparseDataBlock,)
from pymodbus.server import (StartAsyncSerialServer,
                             StartAsyncTcpServer,
                             StartAsyncTlsServer,
                             StartAsyncUdpServer,
                             ServerAsyncStop,)
from pymodbus.server.base import ModbusBaseServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus import __version__ as package_version
import asyncio
from threading import Thread
from pkg.datatype_tool import *

class ModbusServer:
    """Modbus Server"""

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 502,
                 unit_ids: list[int] = [0],
                 comm_type: str = 'tcp',
                 framer_type: str = 'socket',
                 register_type: str = 'full',
                 register_kwargs: dict = None,
                 serial_port: str = '/dev/*',
                 serial_baudrate: int = 9600,
                 serial_stopbits: int = 1,
                 serial_bytesize: int = 8,
                 serial_parity: str = 'N'):
        
        # Validate args
        if type(unit_ids) not in [list, type(None)]:
            raise TypeError('unit_ids type error')
        if register_type not in ['full', 'range', 'spot']:
            raise TypeError('register type error')
        if framer_type not in ['socket', 'rtu', 'ascii', 'tls']:
            raise TypeError('framer type error')
        if comm_type not in ['tcp', 'udp', 'serial', 'tls']:
            raise TypeError('comm type error')

        # Set host
        host = '127.0.0.1' if host == 'localhost' else host
        
        # Define registers
        REGISTERS = [0,  # Discrete output coils
                     1,  # Discrete input coils
                     3,  # Input registers
                     4]  # Holding registers
        
        # Set identity
        IDENTITY = ModbusDeviceIdentification(
            info_name = {'VendorName': 'Nodi',
                         'ProductCode': 'NE',
                         'MajorMinorRevision': package_version,
                         'VendorUrl': 'https://nodi.kr/',
                         'ProductName': 'Edge',
                         'ModelName': 'All',
                         'UserApplicationName': 'Nodi Edge'})
        
        # Define get_datablock method
        def get_datablock(unit_id: int, register: int):
            if register_type == 'full':
                datablock = ModbusSequentialDataBlock.create()
            elif register_type == 'range':
                datablock = ModbusSequentialDataBlock(
                    address=register_kwargs[unit_id][register][0],
                    values=register_kwargs[unit_id][register][1] * [0x00])
            elif register_type == 'spot':
                datablock = ModbusSparseDataBlock(
                    values={loc: 0x00
                            for loc in register_kwargs[unit_id][register]})
            return datablock
            """
            if register_type == 'range':
                register_kwargs = {UNIT_ID1: {0: [LOCATION, LENGTH],
                                              1: [LOCATION, LENGTH],
                                              3: [LOCATION, LENGTH],
                                              4: [LOCATION, LENGTH]}, ...}
            if register_type == 'spot':
                register_kwargs = {UNIT_ID1: {0: [LOCATION1, ...],
                                              1: [LOCATION1, ...],
                                              3: [LOCATION1, ...],
                                              4: [LOCATION1, ...]}, ...}
            """
        
        # Create storage
        self.storage = {}
        
        # If unit IDs configured
        if unit_ids:

            # Create designated unit IDs
            for unit_id in unit_ids:
                if unit_id not in self.storage.keys():
                    self.storage[unit_id] = {}
                for register in REGISTERS:
                    datablock = get_datablock(unit_id, register)
                    self.storage[unit_id][register] = datablock

            # Create slave contexts
            slave_context = {}
            for unit_id in self.storage:
                slave_context[unit_id] = ModbusSlaveContext(
                    di=self.storage[unit_id][1],
                    co=self.storage[unit_id][0],
                    ir=self.storage[unit_id][3],
                    hr=self.storage[unit_id][4])
                
            # Create is_single
            self.is_single = False
        
        # If no unit IDs configured
        else:

            # Create single unit ID
            unit_id = 0
            self.storage[unit_id] = {}
            for register in REGISTERS:
                datablock = get_datablock(unit_id, register)
                self.storage[unit_id][register] = datablock

            # Create slave contexts
            slave_context = ModbusSlaveContext(di=self.storage[unit_id][1],
                                               co=self.storage[unit_id][0],
                                               ir=self.storage[unit_id][3],
                                               hr=self.storage[unit_id][4])
                
            # Create is_single
            self.is_single = True
    
        # Create server context
        self.server_context = ModbusServerContext(slaves=slave_context,
                                                  single=self.is_single)

        # Set server
        if comm_type == 'tcp':
            self.start_method = StartAsyncTcpServer
            self.start_kwargs = {'address': (host, port),
                                 'context': self.server_context,
                                 'framer': framer_type,
                                 'identity': IDENTITY,}
        elif comm_type == 'udp':
            self.start_method = StartAsyncUdpServer
            self.start_kwargs = {'address': (host, port),
                                 'context': self.server_context,
                                 'framer': framer_type,
                                 'identity': IDENTITY,}
        elif comm_type == 'serial':
            self.start_method = StartAsyncSerialServer
            self.start_kwargs = {'port': serial_port,
                                 'baudrate': serial_baudrate,
                                 'stopbits': serial_stopbits,
                                 'bytesize': serial_bytesize,
                                 'parity': serial_parity,
                                 'context': self.server_context,
                                 'framer': framer_type,
                                 'identity': IDENTITY,}
        elif comm_type == 'tls':
            self.start_method = StartAsyncTlsServer
            self.start_kwargs = ...  # NYI
    
    def start_server_fore(self):
        """Start server in foreground"""
        async def _start_server():
            await self.start_method(**self.start_kwargs)
        asyncio.run(_start_server())
        
    def start_server_back(self):
        """Start server in background"""
        loop_thread = Thread(target=self.start_server_fore)
        loop_thread.daemon = True
        loop_thread.start()
    
    def stop_server(self):
        """Stop server"""
        async def _stop_server():
            await ServerAsyncStop()
        asyncio.run(_stop_server())
        del self.storage
    
    def get_server(self):
        return ModbusBaseServer.active_server
    
    def get_unit_ids(self):
        """Get existing unit IDs"""
        return self.server_context.slaves()
    
    def set_values(self,
                   unit_id: int,
                   register: int,
                   location: int,
                   values: list[int]):
        """Set values to server"""
        if self.is_single: unit_id = 0
        storage: ModbusSlaveContext = self.storage[unit_id][register]
        storage.setValues(address=location,
                          values=values)
    
    def get_values(self,
                   unit_id: int,
                   register: int,
                   location: int,
                   length: int) -> list[int]:
        """Get values from server"""
        if self.is_single: unit_id = 0
        storage: ModbusSlaveContext = self.storage[unit_id][register]
        result = storage.getValues(address=location,
                                   count=length)
        return result

from pymodbus.client.tcp import ModbusTcpClient as _ModbusTcpClient

class ModbusTcpClient:
    """Modbus TCP Client"""

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 502,
                 timeout: float = 5.0,
                 retry: int = 3):

        # Interpret localhost
        if host == 'localhost': host = '127.0.0.1'
        
        # Create client
        self.client = _ModbusTcpClient(host=host,
                                       port=port,
                                       timeout=timeout,
                                       retries=retry)
        
        # Define custom function mapping dict
        self.custom_function_md = {1: self._read_bits,
                                   2: self._read_bits,
                                   3: self._read_words,
                                   4: self._read_words,
                                   5: self._write_one,
                                   6: self._write_one,
                                   15: self._write_many,
                                   16: self._write_many}
        
        # Define modbus function mapping dict
        self.modbus_function_md = {1: self.client.read_coils,
                                   2: self.client.read_discrete_inputs,
                                   3: self.client.read_holding_registers,
                                   4: self.client.read_input_registers,
                                   5: self.client.write_coil,
                                   6: self.client.write_register,
                                   15: self.client.write_coils,
                                   16: self.client.write_registers}
        
        # Define block size mapping dict
        self.block_size_md = {1: 125 * 16,
                              2: 125 * 16,
                              3: 125,
                              4: 125,
                              5: None,
                              6: None,
                              15: 800,
                              16: 100}
    
    def connect(self):
        """Connect to server"""

        self.connection = self.client.connect()
        return self.connection
    
    def disconnect(self):
        """Disconnect from server"""
        
        self.client.close()
        self.connection = False
        return self.connection

    def read_any(self,
                 unit_id: int,
                 function_code: int,
                 location: int,
                 length: int) -> list[int]:
        """Read with any function code"""

        # Interpret arguments
        custom_function = self.custom_function_md[function_code]
        modbus_function = self.modbus_function_md[function_code]
        block_size = self.block_size_md[function_code]

        # Execute function and get result
        result = custom_function(unit_id=unit_id,
                                 function=modbus_function,
                                 location=location,
                                 length=length,
                                 block_size=block_size)
        return result

    def write_any(self,
                  unit_id: int,
                  function_code: int,
                  location: int,
                  data_list: list[int]):
        """Write with any function code"""

        # Interpret arguments
        custom_function = self.custom_function_md[function_code]
        modbus_function = self.modbus_function_md[function_code]
        block_size = self.block_size_md[function_code]

        # Execute function and get result
        result = custom_function(unit_id=unit_id,
                                 function=modbus_function,
                                 location=location,
                                 data_list=data_list,
                                 block_size=block_size)
        return result

    def _read_bits(self, unit_id, function, location, length, block_size):
        """Read bits for function code 01/02"""

        # Read numbers over maximum block size
        result = []
        number_reserve = length
        while length > 0:
            result += function(address=location,
                               count=min(block_size, length),
                               slave=unit_id).bits
            location += block_size
            length -= block_size
        return result[0:number_reserve]
    
    def _read_words(self, unit_id, function, location, length, block_size):
        """Read words for function code 03/04"""

        # Read numbers over maximum block size
        result = []
        while length > 0:
            result += function(address=location,
                               count=min(block_size, length),
                               slave=unit_id).registers
            location += block_size
            length -= block_size
        return result

    def _write_one(self, unit_id, function, location, data_list, block_size):
        """Write bit/word for function code 05/06"""

        # Execute writing
        result = function(address=location,
                          value=data_list[0],
                          slave=unit_id)
        return result

    def _write_many(self, unit_id, function, location, data_list, block_size):
        """Write bits/words for function 15/16"""

        # Write numbers over maximum block size
        data_cp = data_list[:]
        while len(data_cp) > 0:
            result = function(address=location,
                              values=data_cp[0:min(block_size,len(data_cp))],
                              slave=unit_id)
            location += block_size
            del data_cp[0:block_size]
        return result

class ModbusTools:

    """Datatype conversion map"""
    DATATYPE_CONV_MAP = {
        ''        : {'size': 1,
                     'get': word1_to_int16,
                     'set': int16_to_word1,},
        'word'    : {'size': 1,
                     'get': word1_to_int16,
                     'set': int16_to_word1,},
        'uint16'  : {'size': 1,
                     'get': word1_to_uint16,
                     'set': uint16_to_word1,},
        'int16'   : {'size': 1,
                     'get': word1_to_int16,
                     'set': int16_to_word1,},
        'uint32'  : {'size': 2,
                     'get': word2_to_uint32,
                     'set': uint32_to_word2,},
        'uint32r' : {'size': 2,
                     'get': word2_to_uint32_reversed,
                     'set': uint32_to_word2_reversed,},
        'int32'   : {'size': 2,
                     'get': word2_to_int32,
                     'set': int32_to_word2,},
        'int32r'  : {'size': 2,
                     'get': word2_to_int32_reversed,
                     'set': int32_to_word2_reversed,},
        'uint64'  : {'size': 4,
                     'get': word4_to_uint64,
                     'set': uint64_to_word4,},
        'int64'   : {'size': 4,
                     'get': word4_to_int64,
                     'set': int64_to_word4,},
        'float32' : {'size': 2,
                     'get': word2_to_float32,
                     'set': float32_to_word2,},
        'float32r': {'size': 2,
                     'get': word2_to_float32_reversed,
                     'set': float32_to_word2_reversed,},
        'float64' : {'size': 4,
                     'get': word4_to_float64,
                     'set': float64_to_word4,},
        'fixed32' : {'size': 2,
                     'get': word2_to_fixed32,
                     'set': fixed32_to_word2,},
        'fixed32r': {'size': 2,
                     'get': word2_to_fixed32_reversed,
                     'set': fixed32_to_word2_reversed,},
        'fixed64' : {'size': 4,
                     'get': word4_to_fixed64,
                     'set': fixed64_to_word4,},
        'char2'   : {'size': 1,
                     'get': word1_to_char2,
                     'set': char2_to_word1,},
        'bit'     : {'size': 1,
                     'get': word1_to_bit,
                     'set': bit_to_word1,},}
    
    def decode_values(self,
                      input_words: list[int],
                      location: int,
                      addresses: list[int],
                      datatypes: list[str],
                      masks: list[int | float],
                      float_decimal: int = 3) -> list[int | float | str]:
        """Convert Modbus words to decoded values"""
        
        # Create output values list
        output_values = []

        # Iterate configs
        for address, datatype, mask in zip(addresses, datatypes, masks):
            
            # Get relative start address and end address
            start_address = address - location
            words_size = self.DATATYPE_CONV_MAP[datatype]['size']
            end_address = start_address + words_size

            # Get conversion function
            conversion_function = self.DATATYPE_CONV_MAP[datatype]['get']

            # Get conversion target words list
            target_words = input_words[start_address:end_address]

            # If datatype is bit, convert with mask
            if datatype == 'bit':
                output_value = conversion_function(*target_words, mask)
                output_value = int(output_value)

            # If datatype is not bit and mask exists, convert then multiple with mask
            elif mask:
                output_value = conversion_function(*target_words) * mask
                output_value = round(output_value, float_decimal)
            
            # If datatype is not bit and no mask exists, just convert
            else:
                output_value = conversion_function(*target_words)

            # Append to output values list
            output_values.append(output_value)
        
        # Return result
        return output_values

    def encode_values(self,
                      input_values: list[int | float | str],
                      location: int,
                      length: int,
                      addresses: list[int],
                      datatypes: list[str],
                      masks: list[int | float]) -> list[int]:
        """Convert encoded values to Modbus words"""

        # Create output words list filled with zero 
        output_words = [0 for _ in range(length)]

        # Iterate configs
        for value, address, datatype, mask in zip(input_values, addresses, datatypes, masks):
            
            # Get relative start address and end address
            start_address = address - location
            words_size = self.DATATYPE_CONV_MAP[datatype]['size']
            end_address = start_address + words_size

            # Get conversion function
            conversion_function = self.DATATYPE_CONV_MAP[datatype]['set']

            # If datatype is bit, convert and cumulate
            if datatype == 'bit':
                if value == 'True' or value == True or value >= 1:
                    output_word = conversion_function(True, mask)
                    output_words[start_address] += output_word
            else:

                # If mask exists, divide by mask
                if mask:
                    if 'int' in datatype or 'word' in datatype:
                        value = int(float(value))
                    elif 'float' in datatype or 'fixed' in datatype:
                        value = float(value) / mask

                # If datatype is not bit, convert
                output_word = conversion_function(value)

                # Convert result to list then append to output words list
                if isinstance(output_word, tuple):
                    output_words[start_address:end_address] = output_word
                else:
                    output_words[start_address:end_address] = [output_word]
        
        # Return result
        return output_words

if __name__ == '__main__':
    ip = input('ip: ')
    port = int(input('port: '))
    unit = int(input('unit: '))
    fc = int(input('fc: '))
    mtc = ModbusTcpClient(ip, port)
    mtc.connect()
    while True:
        addr_loc = int(input('loc: '))
        addr_num = int(input('num: '))
        res = mtc.read_any(unit, fc, addr_loc, addr_num)
        print(res)


#    from time import sleep
#    mts = ModbusServer(host='0.0.0.0',
#                       port=502,
#                       unit_ids=[0])
#    mts.start_server_back()
#    cnt = 0
#    while True:
#        cnt += 1
#        mts.set_values(0, 3, 0, [cnt] * 10)
#        print(mts.get_values(0, 3, 0, 20))
#        sleep(1)
