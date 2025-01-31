import socket
import sys
import argparse
import select

def checkValidPort(port):
   try:
       port = int(args.port)
       if (port < 1 or port > 65535):
           return False
       return True
   except ValueError:
       return False


def validateCLIArguments(args):
   # Validate Client Port Number
   if (not checkValidPort(args.port)):
       print("Invalid Port Number. Must be a integer between 1 and 65535.", file=sys.stderr)
       sys.exit(1)

def parse_request(request):
    lines = request.strip().split("\r\n")
    headers = {}
    for line in lines[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.strip()] = value.strip()
    return lines[0], headers


if __name__ == '__main__':

   parser = argparse.ArgumentParser(description='Server Program.')
   parser.add_argument('--port', required=True, type=int, help='Server Port Number Required. Usage: --port <client port>')
   args = parser.parse_args()

   validateCLIArguments(args)

   server_port = args.port
   local_ip = socket.gethostbyname(socket.gethostname())

   sys.stdout.write(f"Server listening on {local_ip}:{server_port}\n")
   sys.stdout.flush()

   server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
   server_socket.bind(('', server_port))
   server_socket.listen(5)

   registered_client_id = None
   registered_client_ip = None
   registered_client_port = None
   
   registered_client_id_2 = None
   registered_client_ip_2 = None
   registered_client_port_2 = None

   try:
       while True:
           # Use select to monitor both socket and stdin
           readable, _, _ = select.select([server_socket, sys.stdin], [], [], 0.1)
           
           for ready in readable:
               if ready == sys.stdin:
                   command = sys.stdin.readline().strip()
                   if command == "/info":
                       if registered_client_id and registered_client_port:
                           sys.stdout.write(f"{registered_client_id} {registered_client_ip}:{registered_client_port}\n")
                           sys.stdout.flush()
                       if registered_client_id_2 and registered_client_port_2:
                           sys.stdout.write(f"{registered_client_id_2} {registered_client_ip_2}:{registered_client_port_2}\n")
                           sys.stdout.flush()
                       if not (registered_client_id or registered_client_id_2):
                           # sys.stdout.write("No clients registered\n")
                           continue
               
               elif ready == server_socket:
                   client_socket, client_address = server_socket.accept()
                   request = client_socket.recv(4096).decode()
                   request_type, request_headers = parse_request(request)

                   if request_type == "REGISTER":
                       #print("register occured")
                       client_id = request_headers.get("clientID")
                       client_ip = request_headers.get("IP")
                       client_port = request_headers.get("Port")
                       response = (
                           f"REGACK\r\n"
                           f"clientID: {client_id}\r\n"
                           f"IP: {client_ip}\r\n"
                           f"Port: {client_port}\r\n"
                           f"Status: registered\r\n\r\n"
                       )

                       if (registered_client_ip is None or registered_client_port is None):
                           registered_client_id = client_id
                           registered_client_ip = client_ip
                           registered_client_port = client_port
                       else:
                           registered_client_id_2 = client_id
                           registered_client_ip_2 = client_ip
                           registered_client_port_2 = client_port

                       client_socket.send(response.encode())
                       client_socket.close()
                       sys.stdout.write(f"{request_type}: {client_id} from {client_ip}:{client_port} received\n")
                       sys.stdout.flush()

                   elif request_type == "BRIDGE":
                       if (registered_client_ip_2 is None or registered_client_port_2 is None):
                           response = (
                               f"BRIDGEACK\r\n"
                               f"clientID: \r\n"
                               f"IP: \r\n"
                               f"Port: \r\n\r\n"
                           )
                           client_socket.send(response.encode())
                           client_socket.close()

                           sys.stdout.write(f"{request_type}: {registered_client_id} {registered_client_ip}:{registered_client_port}\n")
                           sys.stdout.flush()
                       else:
                           response = (
                               f"BRIDGEACK\r\n"
                               f"clientID: {registered_client_id}\r\n"
                               f"IP: {registered_client_ip}\r\n"
                               f"Port: {registered_client_port}\r\n\r\n"
                           )
                           client_socket.send(response.encode())
                           client_socket.close()

                           sys.stdout.write(f"{request_type}: {registered_client_id} {registered_client_ip}:{registered_client_port} ")
                           sys.stdout.write(f"{registered_client_id_2} {registered_client_ip_2}:{registered_client_port_2}\n")
                           sys.stdout.flush()
   
   except KeyboardInterrupt:
        if (server_socket):
          server_socket.close()
        sys.exit(0)
   except Exception as e:
        sys.stderr.write(f"An error occurred: {e}\n")
        server_socket.close()
        sys.exit(1)
   finally:
        server_socket.close()

