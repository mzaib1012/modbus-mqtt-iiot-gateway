import asyncio
import logging
import random
# Using the modern top-level server class and simulator objects
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

# Setup logging for industrial tracking visibility
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def simulate_factory_data(server):
    """
    Simulates live factory-floor data changing dynamically over time.
    Using the modern async data setter on the server object.
    Holding Registers (func_code=3)
    - Address 1: Temperature (scaled by 10)
    - Address 2: Voltage Grid Parameter
    - Address 3: Power Demand
    """
    device_id = 0x01
    func_code = 3  # Holding Registers
    address = 1
    
    log.info("Factory floor simulator engine started successfully.")
    
    while True:
        await asyncio.sleep(2) # Update factory telemetry every 2 seconds
        
        # Generate typical noisy industrial data
        sim_temp = int(random.uniform(22.0, 28.0) * 10) 
        sim_voltage = int(random.uniform(228.0, 233.0)) 
        sim_power = int(random.uniform(1200.0, 1800.0)) 
        
        try:
            # Modern PyModbus v3.12+ asynchronous value injection
            await server.async_setValues(device_id, func_code, address, [sim_temp, sim_voltage, sim_power])
            log.info(f"PLC Register Update -> Temp: {sim_temp/10}°C, Volts: {sim_voltage}V, Power: {sim_power}W")
        except Exception as e:
            log.error(f"Failed to set register values: {e}")

async def run_server():
    # Modern layout: Define a continuous block of 100 registers initialized with zeroes
    block_def = SimData(address=0, count=100, datatype=DataType.REGISTERS, values=0)
    
    # Bundle the block into a simulated device assigned to ID 1
    device = SimDevice(id=1, simdata=block_def)
    
    # Instantiate the modern Modbus TCP Server engine
    server = ModbusTcpServer(context=device, address=("127.0.0.1", 5020))
    
    # Start the data update loop as a concurrent task, passing the server instance
    asyncio.create_task(simulate_factory_data(server))
    
    # Run the server loop indefinitely
    log.info("Starting Modbus TCP Server on 127.0.0.1:5020")
    await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log.info("Modbus Server shut down safely.")
