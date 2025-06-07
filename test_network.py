import socket
import telnetlib

def test_connectivity():
    """Test network connectivity to SMTP servers"""
    
    hosts_ports = [
        ('smtp.zeptomail.in', 587),
        ('smtp.zeptomail.in', 465),
        ('smtp.zeptomail.in', 25),
        ('smtp.zeptomail.com', 587),
        ('smtp.zoho.in', 587),
    ]
    
    for host, port in hosts_ports:
        try:
            print(f"Testing {host}:{port}...")
            socket.create_connection((host, port), timeout=10)
            print(f"✅ {host}:{port} - Connection successful!")
        except Exception as e:
            print(f"❌ {host}:{port} - Failed: {e}")
    
    print("\n" + "="*50)
    
    # Test with telnet-like connection
    for host, port in hosts_ports:
        try:
            print(f"Telnet test {host}:{port}...")
            tn = telnetlib.Telnet(host, port, timeout=10)
            response = tn.read_until(b'\n', timeout=5)
            print(f"✅ {host}:{port} - Telnet successful: {response.decode().strip()}")
            tn.close()
        except Exception as e:
            print(f"❌ {host}:{port} - Telnet failed: {e}")

if __name__ == "__main__":
    test_connectivity()