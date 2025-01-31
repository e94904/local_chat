import socket
import sys
import argparse
import select
import signal

# Function grabbed from: https://www.geeksforgeeks.org/python-program-to-validate-an-ip-address/
def checkValidIPAddr(ip):
  try:
    socket.inet_aton(ip)
    return True
  except socket.error:
    return False

def checkValidPort(port):
  try:
    port = int(port)
    if (port < 1 or port > 65535):
      return False
    return True
  except ValueError:
    return False

def validateCLIArguments(args):
  # Validate Client ID
  if ((not args.id.isalnum()) or len(args.id) == 0):
    sys.stderr.write("Invalid Client ID. Must only contain letters and numbers.\n")
    sys.exit(1)

  # Validate Client Port Number
  if (not checkValidPort(args.port)):
    sys.stderr.write("Invalid Port Number. Must be a integer between 1 and 65535.\n")
    sys.exit(1)

  # Validate Server Argument
  if (args.server.count(':') != 1):
    sys.stderr.write("Invalid Server Input. Must follow the format serverIP:port.\n")
    sys.exit(1)

  server = args.server.split(':')
  server_ip = server[0]
  server_port = server[1]

  if (not checkValidIPAddr(server_ip)):
    sys.stderr.write("Invalid Server IP Address.\n")
    sys.exit(1)

  if (not checkValidPort(server_port)):
    sys.stderr.write("Invalid Server Input. Server port number must be an integer between 1 and 65535.\n")
    sys.exit(1)

def send_command(server_ip, server_port, message):
  client_socket = None
  try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    
    client_socket.send(message.encode())
    response = client_socket.recv(4096).decode()
    
    client_socket.close()
    
    return response
  except Exception as e:
    sys.stderr.write(f"Communication error: {e}\n")
    if client_socket:
      client_socket.close()    
    return None

def parse_response(response):
  values = [value for value in response.split('\r\n') if value]
  return values

if __name__ == '__main__':

  try:

    # Initialize sockets
    listener_socket = None
    peer_socket = None

    # Signal handler for SIGINT
    def signal_handler(sig, frame):
      if listener_socket:
          listener_socket.close()
      if peer_socket:
          peer_socket.close()
      sys.exit(0)

    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(description='Client Program.')
    parser.add_argument('--id', required=True, help='Client ID Required. Usage: --id <clientID>')
    parser.add_argument('--port', required=True, type=int, help='Client Port Number Required. Usage: --port <client port>')
    parser.add_argument('--server', required=True, help='Server IP and port required. Usage: --server <server ip: port number>')

    args = parser.parse_args()

    validateCLIArguments(args)

    id = args.id
    client_port = args.port
    server = args.server.split(':')
    server_ip = server[0]
    server_port = int(server[1])
    local_ip = socket.gethostbyname(socket.gethostname())

    sys.stdout.write(f"{id} running on {local_ip}:{client_port}\n")
    sys.stdout.flush()

    peer = None # Store Peer Client Information
    registered = False # Whether Client has registered
    bridged = None # Whether Client has bridged
    peer_socket = None # Socket to talk to peer in CHAT mode
    ready_chat = False # Whether Client is in WAIT mode
    in_chat = False # Whether Client is in CHAT mode
    writing_in_chat = False # Wheter Client is writing in CHAT mode

    listener_socket = None
  except KeyboardInterrupt:
    sys.stdout.write("\nTerminating the chat client.\n")
    sys.stdout.write("Exiting Program\n")
    sys.stdout.flush()
    if (listener_socket):
      listener_socket.close()
    if (peer_socket):
      peer_socket.close()
    sys.exit(0)
  except Exception as e:
    sys.stderr.write(f"An error (1) occurred: {e}\n")
    if (listener_socket):
      listener_socket.close()
    if (peer_socket):
      peer_socket.close()
    sys.exit(1)

  # Listener Socket for Accepting Peer Connections
  try: 
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind(('', client_port))
    listener_socket.listen(1)
  except Exception as e:
    sys.stderr.write(f"There was an error in the listener socket: {e}\n")

  sockets = [sys.stdin, listener_socket]
  
  while True:
      
    try:
      readable_sockets, _, _ = select.select(sockets, [], [], 0.1)

      for read_socket in readable_sockets:

        if (in_chat):
          if (writing_in_chat):
            if (read_socket == sys.stdin and peer_socket):
              input = str(sys.stdin.readline().strip())
              if (input == '/quit'):
                message = "QUIT\r\n\r\n\r\n"
                peer_socket.send(message.encode())
                sys.stdout.write("\nTerminating the chat client.\n")
                sys.stdout.write("Exiting Program\n")
                sys.stdout.flush()
                peer_socket.close()
                listener_socket.close()
                sys.exit(0)
              elif (input == '/id'):
                sys.stdout.write(f"{id}\n")
                sys.stdout.flush()
                continue
              
              peer_socket.send(input.encode())
              writing_in_chat = False
            elif (read_socket == peer_socket):
              message = peer_socket.recv(4096).decode()
              if (not message or message == "QUIT\r\n\r\n\r\n"):
                sys.stdout.write("\nTerminating the chat client.\n")
                sys.stdout.write("Exiting Program\n")
                sys.stdout.flush()
                peer_socket.close()
                listener_socket.close()
                sys.exit(0)
            continue
          else:
            if (read_socket == peer_socket):
              message = peer_socket.recv(4096).decode()
              if (not message or message == "QUIT\r\n\r\n\r\n"):
                sys.stdout.write("\nTerminating the chat client.\n")
                sys.stdout.write("Exiting Program\n")
                sys.stdout.flush()
                peer_socket.close()
                listener_socket.close()
                sys.exit(0)
              else:
                sys.stdout.write(f"{message}\n")
                sys.stdout.flush()
                writing_in_chat = True
            elif (read_socket == sys.stdin):
              input = str(sys.stdin.readline().strip())
              if (input == '/quit'):
                message = "QUIT\r\n\r\n\r\n"
                peer_socket.send(message.encode())
                peer_socket.close()
                listener_socket.close()
                sys.exit(0)
              elif (input == '/id'):
                sys.stdout.write(f"{id}\n")
                sys.stdout.flush()
            continue
        if (read_socket == sys.stdin): # If read socket is coming from sys.stdin
            
          input = str(sys.stdin.readline().strip())

          if (input == "/id"):
              
            sys.stdout.write(f"{id}\n")
            sys.stdout.flush()

          elif (input == '/register'):
              
            # Send a REGISTER request to server
            headers = [
                f"clientID: {id}",
                f"IP: {local_ip}",
                f"Port: {client_port}",
            ]
            header_lines = '\r\n'.join(headers)
            message = f"REGISTER\r\n{header_lines}\r\n\r\n"

            response = send_command(server_ip, server_port, message)
            if response:
              registered = True

          elif (input == '/bridge'):
              
            if not registered:
              # sys.stdout.print("Client must register before bridging.\n")
              # sys.stdout.flush()
              continue

            # Send a BRIDGE request to the server
            message = f"BRIDGE\r\nclientID: {id}\r\n\r\n"
            response = send_command(server_ip, server_port, message)
            if response:
                
              bridged = True
              response_lines = parse_response(response)

              response_type = response_lines[0]
              headers = response_lines[1:]
              peer_id = headers[0].split(':')[1].strip()
              peer_ip = headers[1].split(':')[1].strip()
              peer_port = headers[2].split(':')[1].strip()

              if (peer_id and peer_ip and peer_port):
                peer = {'clientID': peer_id, 'IP': peer_ip, 'Port': int(peer_port)}
                # sys.stdout.write(f"Received peer information: {peer}\n")
              else:
                # sys.stdout.write(f"No peer information available. Entering WAIT state.\n")
                ready_chat = True
          
          elif (input == '/chat'):

            if (not bridged):
              # sys.stdout.print("Client must bridge before chatting.\n")
              # sys.stdout.flush()
              continue
            if (peer is not None):
              try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer['IP'], peer['Port']))

                headers = [
                  f"clientID: {id}",
                  f"IP: {local_ip}",
                  f"Port: {client_port}",
                ]
                header_lines = '\r\n'.join(headers)
                message = f"CHAT\r\n{header_lines}\r\n\r\n"

                peer_socket.send(message.encode())
                sockets.pop()
                sockets.append(peer_socket)

                in_chat = True
                writing_in_chat = True
              except Exception as e:
                sys.stderr.write(f"Communication socket error with peer: {e}\n")
                peer_socket.close()
                continue
            else:
              # sys.stdout.print("Cannot enter CHAT mode in WAIT state.\n")
              # sys.stdout.flush()
              continue

          elif (input == '/quit'):
            # sys.stdout.write("Exiting...\n")
            listener_socket.close()
            sys.exit(0)
          else:
            continue
        
        elif ready_chat and read_socket == listener_socket:

          peer_socket, peer_addr = listener_socket.accept()

          response = peer_socket.recv(4096).decode().strip()

          if response:

            response_lines = parse_response(response)

            headers = response_lines[1:]
            peer_id = headers[0].split(':')[1].strip()
           
            # TEMPORARY FOR PIPELINE
            peer_ip = None
            peer_port = None

            if (len(headers) >= 2):
              peer_ip = headers[1].split(':')[1].strip()
            if (len(headers) >= 3):
              peer_port = headers[2].split(':')[1].strip()
            
            sockets.pop()
            sockets.append(peer_socket)
            sys.stdout.write(f"Incoming chat request from {peer_id} {peer_ip}:{peer_port}\r\n")
            sys.stdout.flush()

            in_chat = True
            writing_in_chat = False
    
    except KeyboardInterrupt:
        sys.stdout.write("\nTerminating the chat client.\n")
        sys.stdout.write("Exiting Program\n")
        sys.stdout.flush()
        if (listener_socket):
          listener_socket.close()
        if (peer_socket):
          peer_socket.close()
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"An error (2) occurred: {e}\n")
        if (listener_socket):
          listener_socket.close()
        if (peer_socket):
          peer_socket.close()
        sys.exit(1)
