import socket
import struct
import time
import random


def simple_snmp_server(host='localhost', port=161):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"Simple SNMP-like simulator listening on {host}:{port}")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received request from {addr}")

            # Parse the request (just get the last byte as the OID)
            if not data:
                print("Received empty request, ignoring")
                continue
            oid = data[-1]

            # Generate a response based on the OID
            if oid == 0:  # sysUpTime
                value = int(time.time() * 100) % (2 ** 32)  # Ensure it fits in 32 bits
            elif oid == 1:  # ifInOctets
                value = random.randint(0, 1000000)
            elif oid == 2:  # ifOutOctets
                value = random.randint(0, 1000000)
            elif oid == 3:  # cpuUsage
                value = random.randint(0, 100)
            else:
                print(f"Received unknown OID: {oid}")
                value = 0

            # Send the response
            response = struct.pack('!I', value)
            sock.sendto(response, addr)
        except Exception as e:
            print(f"Error processing request: {e}")


if __name__ == "__main__":
    simple_snmp_server()