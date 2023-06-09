from pymodbus.server.async_io import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.client import ModbusTcpClient
from pymodbus.pdu import ModbusResponse
import threading
import time

from raspberry.config import ip_address as raspberry_ip
from utils.logger import get_logger

class ModbusServer:
    def __init__(self, initial_coil_states=[False, False, False], host=raspberry_ip, port=502):
        self.initial_coil_states = initial_coil_states
        self.host = host
        self.port = port
        self.logger = get_logger(__name__, self.__class__.__name__)

        # Create a datastore and initialize it with a coil at address 000001 set to False
        self.store = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, self.initial_coil_states)
        )
        self.context = ModbusServerContext(slaves=self.store, single=True)

        # Create a Modbus device identification
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = 'Pymodbus'
        self.identity.ProductCode = 'PM'
        self.identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
        self.identity.ProductName = 'Pymodbus Server'
        self.identity.ModelName = 'Pymodbus Server'
        self.identity.MajorMinorRevision = '1.0'
    
    def setup(self):
        # Write the initial state to the coil
        self.store.setValues(1, 0, self.initial_coil_states)
        self.logger.info("modbus server setup finished...")

    
    def run(self):
        setup_thread = threading.Thread(target=self.setup)
        setup_thread.start()

        while True:
            try:
                self.logger.info(f"starting server at {self.host}:{self.port}")
                self.server = StartTcpServer(context=self.context, identity=self.identity, address=(self.host, self.port))
            except OSError as e:
                self.logger.error(f"OSError occurred, retrying after 3 seconds... Error: {e}")
                time.sleep(3)
                continue
            break


class ModbusClient:
    def __init__(self, host=raspberry_ip, port=502):
        self.host = host
        self.port = port
        self.client = ModbusTcpClient(self.host, self.port)
        self.logger = get_logger(__name__, self.__class__.__name__)

    def read_coil(self, coil_addr):
        response:ModbusResponse = self.client.read_coils(coil_addr, 1)
        if response.isError():
            self.logger.error(f"Error reading coil at address {coil_addr}")
        else:
            self.logger.debug(f"read value: {response} from coild address: {coil_addr}")
            return response.bits[0]

    def write_coil(self, coil_addr, value):
        response:ModbusResponse = self.client.write_coil(coil_addr, value)
        if response.isError():
            self.logger.error(f"Error writing coil at address {coil_addr}, resp: {response}")
        else:
            self.logger.debug(f"value: {value} written at coild address: {coil_addr}")