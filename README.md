## Custom Bit-Level IIoT Edge Data Gateway

An ultra-lightweight, containerized Industrial Internet of Things (IIoT) edge gateway engine written in pure Python. This engine establishes low-level socket connections to poll legacy industrial Modbus TCP devices, performs runtime engineering-unit serialization, and streams structured, decoupled JSON payloads out to cloud-based MQTT infrastructure.

By handling the protocol stack natively at the byte layer, this architecture completely bypasses heavy third-party libraries—optimizing hardware footprint, eliminating dependency drifting, and maintaining absolute deterministic timing for edge-computing topologies.

---

## Architecture Overview
The gateway operates as a high-performance translation link between Operational Technology (OT) plant-floor environments and Information Technology (IT) enterprise cloud networks.

1. **OT Ingestion Layer:** The gateway opens an asynchronous standard TCP socket to target programmable logic controllers (PLCs), smart meters, or power transformers. It manually packs network big-endian command packets to fetch industrial parameters directly.
2. **Serialization & Scaling Engine:** Raw 16-bit unsigned integer data payloads collected from the registers are systematically unpacked via bitmask mappings, scaled by precision floats, and encapsulated into unified semantic JSON profiles.
3. **IT Cloud Publish Layer:** The processed telemetry stream is asynchronously dispatched to a distributed MQTT broker over port 1883 with Quality of Service (QoS 1) configurations to guarantee delivery.

---

## Deep-Dive: Bit-Level Modbus TCP Frame Construction
Rather than relying on abstract wrapper libraries, this gateway interacts directly with the network interface. To poll holding registers `1` through `3` from an active device mapped to Slave ID `1`, the gateway dynamically synthesizes an exact 12-byte binary packet using the `struct` serialization configuration (`>HHHBBHH`):

| Layer | Field Name | Hex Value | Size / Type | Technical Description |
| :--- | :--- | :--- | :--- | :--- |
| **MBAP Header** | Transaction Identifier | `0x00 0x01` | 2 Bytes (16-bit UInt) | Unique identifier for request/response synchronization. |
| | Protocol Identifier | `0x00 0x00` | 2 Bytes (16-bit UInt) | `0` strictly isolates the standard Modbus TCP protocol. |
| | Length Field | `0x00 0x06` | 2 Bytes (16-bit UInt) | Specifies that exactly 6 bytes follow this field. |
| | Unit Identifier (Slave ID) | `0x01` | 1 Byte (8-bit UInt) | Logical address of the target controller on the network segment. |
| **PDU Payload** | Function Code | `0x03` | 1 Byte (8-bit UInt) | Standard command code to Read Holding Registers. |
| | Starting Address | `0x00 0x01` | 2 Bytes (16-bit UInt) | Data register index mapping to the primary sensor block. |
| | Quantity of Registers | `0x00 0x03` | 2 Bytes (16-bit UInt) | Requests exactly 3 continuous 16-bit records (6 total data bytes). |

### Binary Packaging Implementation
```python
# Pure Python binary framing structure
request = struct.pack(">HHHBBHH", 
                      transaction_id, # H (16-bit)
                      protocol_id,    # H (16-bit)
                      length,         # H (16-bit)
                      unit_id,        # B (8-bit)
                      function_code,  # B (8-bit)
                      start_addr,     # H (16-bit)
                      count)          # H (16-bit)

```

---

## Configuration Mapping (`gateway_config.json`)

The mapping logic is fully decoupled from the core execution engine. Industrial sensors can be re-addressed, recalibrated, or re-routed onto new MQTT channels by modifying the declarative JSON manifest without altering a single line of executable code:

```json
{
  "modbus": {
    "host": "127.0.0.1",
    "port": 5020,
    "slave_id": 1,
    "polling_interval_seconds": 2,
    "registers": [
      {
        "address": 1,
        "name": "temperature_celsius",
        "scale": 0.1,
        "description": "Primary transformer hot-spot temperature sensor"
      },
      {
        "address": 2,
        "name": "grid_voltage_v",
        "scale": 1.0,
        "description": "Incoming phase-to-neutral utility line voltage"
      },
      {
        "address": 3,
        "name": "load_power_w",
        "scale": 1.0,
        "description": "Active power draw from industrial motor load"
      }
    ]
  },
  "mqtt": {
    "broker": "broker.hivemq.com",
    "port": 1883,
    "base_topic": "factory/iiot/gateway_01/telemetry",
    "client_id": "iiot_edge_gateway_v1"
  }
}

```

---

## Production Deployment & Containerization

The system is built for resource-constrained embedded edge computers (e.g., Advantech, Moxa, or Raspberry Pi nodes running IoT Edge runtimes). It utilizes a lightweight Docker container base.

### Building the Image

```bash
docker build -t iiot-edge-gateway:latest .

```

### Running the Infrastructure Locally

To launch the containerized gateway with host network alignment for telemetry processing:

```bash
docker run -d \
  --name iiot_gateway_instance \
  --network="host" \
  --restart unless-stopped \
  iiot-edge-gateway:latest

```

---

## Key Engineering Metrics Demonstrated

* **Bit-Stream Literacy:** Bypasses abstract libraries to parse and unpack raw network binary buffers utilizing Python `struct` maps.
* **Decoupled Architecture:** Segregates OT hardware registers, mathematical engineering scales, and IT cloud topics into distinct external configurations.
* **Error-Handling & Stability:** Embedded network timeouts, socket isolation mechanics, and auto-reconnection loops prevent edge gateway freezing on remote network drops.

---

## Repository Tree Structure

```text
iiot-edge-data-gateway/
├── mock_device/
│   └── mock_modbus_server.py             # Asynchronous PyModbus factory simulator hardware
├── src/
│   ├── gateway.py                        # Core low-level socket data gateway application
│   └── gateway_config.json               # Decoupled register-to-cloud topology mapping configuration
├── Dockerfile                            # Multi-stage lightweight deployment container manifest
├── requirements.txt                      # Minimum explicit system dependency references
├── server_runtime.log
└── README.md                             # Comprehensive technical engineering blueprint

```

```

```
