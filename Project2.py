import socket
import os 
import struct 
import time

# ICMP message types
ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


# Calculate the checksum for the ICMP packet
def checksum(data):
    # If the length of the data is odd, add a padding byte
    if len(data) % 2:
        data += b'\x00'
    # Calculate the checksum using 16-bit words
    words = struct.unpack('!%s' % ('H' * (len(data) // 2)), data)
    csum = sum(words)
    csum = (csum >> 16) + (csum & 0xffff)
    csum += (csum >> 16)
    return (~csum) & 0xffff

# Send an ICMP echo request to the given host
def ping(host):
    # Create a raw socket using ICMP protocol
    with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
        # Set the timeout for receiving the reply to 1 second
        sock.settimeout(1)

        # Generate a unique ID for the ICMP packet
        pid = os.getpid() & 0xFFFF

        # Encode the payload data with the current timestamp
        payload = struct.pack('d', time.time())

        # Build the ICMP echo request packet
        packet = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, pid, 1, payload)
        chksum = checksum(packet)
        packet = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, chksum, pid, 1, payload)

        # Send the packet to the target host
        sock.sendto(packet, (host, 1))

        # Wait for the reply from the target host
        try:
            data, addr = sock.recvfrom(1024)
            icmp_type, code, chksum, pid, seq, timestamp = struct.unpack('!BBHHHd', data[20:])

            # Check that the reply is an ICMP echo reply with matching ID and sequence numbers
            if icmp_type == ICMP_ECHO_REPLY and pid == os.getpid() & 0xFFFF and seq == 1:
                # Calculate the round-trip time
                rtt = (time.time() - timestamp) * 1000
                print(f"Ping reply from {addr[0]}: rtt={rtt:.3f} ms")
            else:
                print("Received invalid ICMP reply")
        except socket.timeout:
            print("Request timed out")
        except socket.error as e:
            print(f"Receiving reply failed: {e}")

# Run the Ping client and send packets to the given host every second
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ping a host using ICMP')
    parser.add_argument('host', help='the target host to ping')
    args = parser.parse_args()

    while True:
        print("Pinging {args.host}...")
        ping(args.host)
        time.sleep(1)
