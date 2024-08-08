import socket
import struct
import time


def simple_snmp_get(host='localhost', port=161, oid=0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    try:
        # Send a request (just send the OID as a single byte)
        sock.sendto(bytes([oid]), (host, port))

        data, _ = sock.recvfrom(1024)
        if len(data) != 4:
            print(f"Received unexpected data length: {len(data)} bytes")
            return None
        value = struct.unpack('!I', data)[0]
        return value
    except socket.timeout:
        print(f"Timeout while querying {host} for OID {oid}")
        return None
    except Exception as e:
        print(f"Error querying {host} for OID {oid}: {e}")
        return None
    finally:
        sock.close()


def collect():
    oids = {
        'sysUpTime': 0,
        'ifInOctets': 1,
        'ifOutOctets': 2,
        'cpuUsage': 3
    }

    results = {}
    for oid_name, oid in oids.items():
        value = simple_snmp_get(oid=oid)
        if value is not None:
            results[oid_name] = value

    return results


if __name__ == "__main__":
    start_time = time.time()
    result = collect()
    end_time = time.time()
    print(f"Simple SNMP-like Collection Results: {result}")
    print(f"Collection took {end_time - start_time:.2f} seconds")