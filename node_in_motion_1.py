# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 00:12:39 2026

@author: stewarta6
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 10:23:18 2026

@author: ataly
"""

import socket
import threading
import json
import time
import uuid
DEFAULT_PORT = 50505
MAX_HOPS = 50

#UDP heartbeat settings
HEARTBEAT_INTERVAL = 3 #send a heartbeat every 5 seconds 
HEARTBEAT_TIMEOUT = 5 #Mark a neighbor dead after 15 seconds

#unique ID
NODE_ID = str(uuid.uuid4())
MY_NAME = input("Your unique name (example Salem-O): ").strip()
MY_STAMP = input("Your one-word stamp: ").strip()
MY_PORT = int(input(f"Your listening port [{DEFAULT_PORT}]: ") or DEFAULT_PORT)

#collecting your neighbors
NUM_NEIGHBORS = int (input("How many neighbors do you have: "))
neighbors = {}

# A lock protects neighbor information shared between threads.
neighbors_lock = threading.Lock()

#populating a dictionary  with ip address, whether it is alive or not, and if its still alive
for i in range(NUM_NEIGHBORS):
    ip = input(f"Enter neighbor {i + 1} IP address: ")
    port = int(input(f"Enter neighbor {i + 1} port: "))
    
    neighbors[f"Neighbor {i+1}"]= {
        "ip_addr": ip,
        "port": port,
        "status": "unknown",
        "last_seen": None
        }
      
    #how much neighbors do we have
print(f"Your node has {NUM_NEIGHBORS} neighbors")

#debugging tool
#for i in range(len(neighbors)):
 #   print(f"Neighbor{i+1}: {neighbors[i]}")
    

node = {
      "node_id" : NODE_ID,
      "node_port" : MY_PORT,
      "neighbors" : neighbors
      }
NEXT_PORT = int(input(f"Next students port [{DEFAULT_PORT}]: ") or DEFAULT_PORT)


print("=====NODE INFORMATION=====" )
print(f"Node ID: {node['node_id']}")

print(f"Number of neighbors: {NUM_NEIGHBORS}")
i=1
for n in neighbors:
    print(f"Neighbor {i}: {n}")
    i=i+1



ready_event = threading.Event()

def listen_for_heartbeats():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:   
     udp_sock.bind(("0.0.0.0", MY_PORT))
     print(f"UDP HEARTBEAT: Listening on port {MY_PORT}")
     
     while True:
         try:
             # Receive heartbeat data and the sender's address.
               data, addr = udp_sock.recvfrom(1024)
      
               sender_ip= addr[0]
               # Convert the received bytes into a string.
               message = data.decode("utf-8").strip()

               # Expected format: HEARTBEAT|NodeName|Timestamp
               parts = message.split("|")

               if len(parts) != 3 or parts[0] != "HEARTBEAT":
                  continue

               sender_name = parts[1]

               # Find the neighbor that sent the heartbeat.
               with neighbors_lock:

                    for name, info in neighbors.items():

                        if info["ip_addr"] == sender_ip:

                            # Update the neighbor's status and timestamp.
                            info["status"] = "alive"
                            info["last_seen"] = time.time()
                            print(f"{name} is alive")

                            print(
                                f"Heartbeat received from "
                                f"{sender_name} ({sender_ip})"
                            )

                            break

         except (OSError, UnicodeDecodeError) as error:
            print("Heartbeat receiving error:", error)
            
def send_heartbeats():
    """Send UDP heartbeat messages to all configured neighbors."""

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        while True:

     # Create a heartbeat message with our name and timestamp.
            message = (
               f"HEARTBEAT|{MY_NAME}|{time.time()}"
           ).encode("utf-8")

           # Make a safe copy of the neighbor information.
            with neighbors_lock:
               neighbor_list = list(neighbors.items())

           # Send the heartbeat to every neighbor.
            for name, info in neighbor_list:

               try:
                   destination = (
                       info["ip_addr"],
                       info["port"]
                   )

                   udp_sock.sendto(message, destination)

               except OSError as error:
                   print(f"Could not send heartbeat to {name}: {error}")

           # Wait before sending the next heartbeat.
            time.sleep(HEARTBEAT_INTERVAL)
    
def monitor_neighbors():
    while True:
        for name, info in neighbors.items():
            if info["last_seen"] is not None:
                elapsed_time = time.time() - info["last_seen"]
                
                if elapsed_time > HEARTBEAT_TIMEOUT:
                   if info["status"] != "unavailable":
                    neighbors[name]["status"] = "unavailable"
                    print(f"{name} is now unavailable")
        time.sleep(2)
        
def receive_json(conn):
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(1024)
        if not chunk:
            break
        data += chunk
        if len(data) > 65536:
            raise ValueError("Token is too large")

    if not data:
        return None

    return json.loads(data.decode("utf-8").strip())

def send_token(token):
    if token["ttl"] <= 0:
        print("STOPPED: TTL reached zero. The ring may be configured incorrectly.")
        return

    token["hops"] += 1
    token["ttl"] -= 1
    payload = (json.dumps(token) + "\n").encode("utf-8")

    for attempt in range(1, 6):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.settimeout(4)

                # TODO 1: Connect to NEXT_IP and NEXT_PORT.
                client.connect((NEXT_IP, NEXT_PORT))
                
                # TODO 2: Send the entire payload.
                client.sendall(payload)

            print(f"FORWARDED to {NEXT_IP}:{NEXT_PORT}")
            return

        except OSError as error:
            print(f"Attempt {attempt}/5 failed: {error}")           
            time.sleep(2)

    print("BROKEN LINK: Could not reach the next student after 5 attempts.")

def process_token(token):
    print("\nTOKEN RECEIVED")
    print("Message:", token["message"])
    print("Route so far:", " -> ".join(token["path"]))

    # Is this MY token returning home?
    if token["origin"] == MY_NAME and token["hops"] > 0:
        token["path"].append(MY_NAME)
        elapsed = time.time() - token["started_at"]

        print("\n*** TOKEN MADE IT HOME! ***")
        print("Message:", token["message"])
        print("Route:", " -> ".join(token["path"]))
        print("Stamps:", " | ".join(token["stamps"]))
        print("Hops:", token["hops"])
        print("Lap time:", round(elapsed, 2), "seconds")
        return

    # Safety check: a non-origin node should not appear twice.
    if MY_NAME in token["path"]:
        print("LOOP DETECTED: This node was visited already. Token stopped.")
        return

    # TODO 3: Append MY_NAME to token["path"].
    token["path"].append(MY_NAME)
    
    # TODO 4: Append MY_STAMP to token["stamps"].
    token["stamps"].append(MY_STAMP)
    
    print("Updated route:", " -> ".join(token["path"]))
    send_token(token)

def listen_forever():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # TODO 5: Bind to ("0.0.0.0", MY_PORT).
        server.bind(("0.0.0.0", MY_PORT))
        
        # TODO 6: Put the socket into listening mode.
        server.listen(30)
        print(f"READY: {MY_NAME} is listening on port {MY_PORT}")
        ready_event.set()

        while True:
            # TODO 7: Accept an incoming connection.
            conn, addr = server.accept();
            # Store the connected socket in conn and the address in addr.

            with conn:
                try:
                    token = receive_json(conn)
                    if token is not None:
                        process_token(token)
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                    print("Bad token received:", error)

def create_new_token(message):
    return {
        "token_id": uuid.uuid4().hex[:8],
        "origin": MY_NAME,
        "message": message,
        "path": [MY_NAME],
        "stamps": [MY_STAMP],
        "hops": 0,
        "ttl": MAX_HOPS,
        "started_at": time.time()
    }

listener = threading.Thread(target=listen_forever, daemon=True)
listener.start()
ready_event.wait()
receiver_thread = threading.Thread(
    target=listen_for_heartbeats,
    daemon=True
)

sender_thread = threading.Thread(
    target=send_heartbeats,
    daemon=True
)

receiver_thread.start()
sender_thread.start()

print("\nYour node is ready.")
print("Do not send until the instructor says GO.")

while True:
    command = input("\nType SEND to start a token, or QUIT: ").strip().upper()

    if command == "SEND":
        message = input("Message to send around the ring: ").strip()
        if message:
            send_token(create_new_token(message))
        else:
            print("Message cannot be empty.")

    elif command == "QUIT":
        print("Closing node.")
        break

    else:
        print("Please type SEND or QUIT.")
