import socket
import json
import time
import logging
import struct
import paho.mqtt.client as mqtt

# Setup logging architecture
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("IIoT_Gateway")

def load_configuration(config_path="gateway_config.json"):
    """Loads operational thresholds and endpoints from structural JSON configuration."""
    with open(config_path, "r") as file:
        return json.load(file)

def read_modbus_registers_raw(host, port, unit_id, start_addr, count):
    """
    Polls Modbus TCP registers directly using native sockets.
    Demonstrates true low-level protocol comprehension.
    """
    transaction_id = 1
    protocol_id = 0
    length = 6 # 6 bytes follow the length field (UnitID + FuncCode + Addr + Count)
    function_code = 3 # Read Holding Registers
    
    # FIXED: Format string changed to '>HHHBBHH' to match the 7 positional items precisely
    request = struct.pack(">HHHBBHH", 
                          transaction_id, 
                          protocol_id, 
                          length, 
                          unit_id, 
                          function_code, 
                          start_addr, 
                          count)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        s.connect((host, port))
        s.sendall(request)
        
        # Modbus response header is 9 bytes minimum (MBAP Header + Unit ID + Function Code + Byte Count)
        header = s.recv(9)
        if len(header) < 9:
            return None
        
        # Unpack header up to the last byte to extract byte count
        # Header structure: Transaction(2), Protocol(2), Length(2), Unit(1), FuncCode(1), ByteCount(1)
        _, _, _, _, _, byte_count = struct.unpack(">HHHBBB", header)
        
        # Read the remaining data registers payload based on what the server claimed it sent
        data_payload = s.recv(byte_count)
        if len(data_payload) < byte_count:
            return None
        
        # Unpack data payload integers (Each register is 2 bytes -> 'H')
        register_format = ">" + "H" * count
        return list(struct.unpack(register_format, data_payload))

def run_gateway():
    config = load_configuration()
    m_cfg = config["modbus"]
    q_cfg = config["mqtt"]
    
    log.info("Initializing Custom Bit-Level IIoT Gateway Engine...")
    
    # Initialize Cloud MQTT Client
    mqtt_client = mqtt.Client(client_id=q_cfg["client_id"], callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        log.info(f"Connecting to Cloud MQTT Broker at {q_cfg['broker']}:{q_cfg['port']}...")
        mqtt_client.connect(q_cfg["broker"], q_cfg["port"], keepalive=60)
        mqtt_client.loop_start()
        log.info("Cloud MQTT Broker connection initialized successfully.")
    except Exception as e:
        log.error(f"Failed to connect to MQTT Broker: {e}.")
        return

    try:
        while True:
            addresses = [reg["address"] for reg in m_cfg["registers"]]
            start_address = min(addresses)
            count = len(addresses)
            
            # Poll data raw via custom socket engine
            raw_values = read_modbus_registers_raw(
                m_cfg["host"], 
                m_cfg["port"], 
                m_cfg["slave_id"], 
                start_address, 
                count
            )
            
            if raw_values is None or len(raw_values) < count:
                log.error("Modbus frame parsing timeout or corrupted telemetry received.")
            else:
                payload = {
                    "timestamp": float(time.time()),
                    "gateway_id": q_cfg["client_id"],
                    "telemetry": {}
                }
                
                # Dynamically scale and serialize metrics
                for i, reg in enumerate(m_cfg["registers"]):
                    raw_val = raw_values[i]
                    processed_val = round(raw_val * reg["scale"], 2)
                    payload["telemetry"][reg["name"]] = processed_val
                
                json_payload = json.dumps(payload, indent=2)
                
                # Publish to HiveMQ Cloud Broker
                mqtt_topic = q_cfg["base_topic"]
                mqtt_client.publish(mqtt_topic, json_payload, qos=1)
                log.info(f"Data Published cleanly to MQTT topic [{mqtt_topic}]:\n{json_payload}")
                
            time.sleep(m_cfg["polling_interval_seconds"])
            
    except KeyboardInterrupt:
        log.info("Received interrupt sequence. Safe shutdown initiated.")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        log.info("IIoT Gateway safely dormant.")

if __name__ == "__main__":
    run_gateway()
