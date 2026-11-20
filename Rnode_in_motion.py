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
    name = input("Enter node name:")
    ip = input(f"Enter neighbor {i + 1} IP address: ")
    port = int(input(f"Enter neighbor {i + 1} port: "))
    
    neighbors[name]= {
        "name" : name,
        "ip_addr": ip,
        "port": port,
        "status": "unknown",
        "last_seen": None,
        "destinations" : []
        }
      
    #how much neighbors do we have
print(f"Your node has {NUM_NEIGHBORS} neighbors")
print(neighbors)
#debugging tool
#for i in range(len(neighbors)):
 #   print(f"Neighbor{i+1}: {neighbors[i]}")
    

node = {
      "node_id" : NODE_ID,
      "node_port" : MY_PORT,
      "neighbors" : neighbors
      }
# Get the primary next students IP and port
PRIMARY = input("Primary node:")

with neighbors_lock:
    for n in neighbors.values():
        if n["name"] == PRIMARY:
            NEXT_IP= n["ip_addr"]
            NEXT_PORT = n["port"]


# Routing Table Initialization

# Stores all possible routes to neighboring nodes.
routing_table = {}

# A lock protects routing table information shared between threads.
routing_table_lock = threading.Lock()

# Add every configured neighbor as a possible route.
for name, info in neighbors.items():

    routing_table[name] = {
        "ip_addr": info["ip_addr"],
        "port": info["port"],
        "status": "unknown",
        "last_seen": None,
        "is_primary": (
            info["ip_addr"] == NEXT_IP
            and info["port"] == NEXT_PORT
        ),
        "destinations": info["destinations"]
    }

print("\n===== ROUTING TABLE =====")

for name, route in routing_table.items():
    print(
        f"{name}: {route['ip_addr']}:{route['port']} | "
        f"Status: {route['status']} | "
        f"Primary: {route['is_primary']}"
    )


print("=====NODE INFORMATION=====" )
print(f"Node ID: {node['node_id']}")

print(f"Number of neighbors: {NUM_NEIGHBORS}")
i=1
for n in neighbors:
    print(f"Neighbor {i}: {n}")
    i=i+1

ready_event = threading.Event()

# UDP Heartbeat Functions

def listen_for_heartbeats():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:   
     udp_sock.bind(("0.0.0.0", MY_PORT))
     print(f"UDP HEARTBEAT: Listening on port {MY_PORT}")
     
     while True:
         try:
             # Receive heartbeat data and the sender's address.
               data, addr = udp_sock.recvfrom(1024)
               print("PACKET ARRIVED:", data)
               sender_ip= addr[0]
               # Convert the received bytes into a string.
               message = data.decode("utf-8").strip()

               # Expected format: HEARTBEAT|NodeName|Timestamp
             
               parts = message.split("|")
              
               if len(parts) != 3 or parts[0] != "HEARTBEAT":
                  continue

               sender_name = parts[1]

               # Find the neighbor that sent the heartbeat.
               if sender_name not in neighbors:
                   continue
               
               mark_neighbor_available(sender_name)
            #   print("LAST SEEN:", neighbors[sender_name]["last_seen"])
             #  print("STATUS:", neighbors[sender_name]["status"])
              # print(f"{sender_name} is alive")
               #print(
                 # f"Heartbeat received from "
                  # f"{sender_name} ({sender_ip})"
                   
                #)
               
                            

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
#temp
               try:
                   destination = (
                       info["ip_addr"],
                       info["port"]
                   )
                   print(f"Heartbeat sent to {name} at {destination}")
                   udp_sock.sendto(message, destination)

               except OSError as error:
                   print(f"Could not send heartbeat to {name}: {error}")

           # Wait before sending the next heartbeat.
            time.sleep(HEARTBEAT_INTERVAL)
    
    #checks every neighbor and updates status using node unavailble method to check if its still alive
def monitor_neighbors():
    while True:
        
        with neighbors_lock:
            neighbor_names = list(neighbors.keys())
        for name in neighbor_names:
            mark_neighbor_unavailable(name)
            
        time.sleep(2)
        
    #filtering method to find alive nodes
def active_neighbors():
    active_neighbors= {}
    with neighbors_lock:
        for n, status in neighbors.items():
            if status["status"]== "alive":
                active_neighbors[n]=status
    return active_neighbors

#set primary neighbor
def promote_backup():
    with routing_table_lock:

        # Find the current primary
        for name, info in routing_table.items():

            if info["is_primary"] and info["status"] == "unavailable":

                # Find an available backup
                for backup_name, backup_info in routing_table.items():

                    if (
                        backup_info["status"] == "alive"
                        and not backup_info["is_primary"]
                    ):
                        backup_info["is_primary"] = True
                        info["is_primary"] = False

                        print(f"{backup_name} is now the primary!")
                        return

        print("No available backup neighbors.")
# Routing Funtions 
def get_next_hop(destination, attempted_neighbors=None):
    """Choose the primary neighbor first, then an available neighbor."""
    if attempted_neighbors is None:
        attempted_neighbors = set()

    with routing_table_lock:

        routes = list(routing_table.items())

        # Find neighbors that are alive, can reach the destination,
        # and have not already been attempted.
        valid_routes = [
            (name, info) for name, info in routes
            if destination in info["destinations"]
            and info["status"] == "alive"
            and name not in attempted_neighbors
        ]

        # Prefer the primary neighbor.
        primary = [
            (name, info) for name, info in valid_routes
            if info["is_primary"]
        ]

        if primary:
            return primary[0]

        # Otherwise, choose a valid backup.
        backups = [
            (name, info) for name, info in valid_routes
            if not info["is_primary"]
        ]

        if backups:
            return backups[0]

        return None
  
def mark_neighbor_unavailable(name):
    """Update both dictionaries when a neighbor fails."""

    with neighbors_lock:
        #does name exist
        if name not in neighbors:
            return
        
        if neighbors[name]["status"] == "unavailable":
            return
        last_seen= neighbors[name]["last_seen"]
        
        #havent received a heartbeat
        if last_seen is None:
            return
        
        elapsed_time = time.time()- last_seen
        
        if elapsed_time <= HEARTBEAT_TIMEOUT:
            return
        with routing_table_lock:
            neighbors[name]["status"] = "unavailable"
            if name in routing_table:
                routing_table[name]["status"] = "unavailable"
    print(f"{name} is now unavailable")
    promote_backup()

#update both dictionaries for when a node is alive
def mark_neighbor_available(name):
   with neighbors_lock:
        if name not in neighbors:
            return

        previous_status = neighbors[name]["status"]

        neighbors[name]["status"] = "alive"
        neighbors[name]["last_seen"] = time.time()

        if previous_status != "alive":
            print(f"{name} is alive")

   with routing_table_lock:
       
       if name in routing_table:
           routing_table[name]["status"] = "alive"
           routing_table[name]["last_seen"] = time.time()
            
# TOKEN RECEIVING AND SENDING FUNCTIONS
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

def send_token(token, attempted_neighbors=None):

    if attempted_neighbors is None:
        attempted_neighbors = set()

    if token["ttl"] <= 0:
        print("STOPPED: TTL reached zero.")
        return

    next_hop = get_next_hop(
        token["destination"],
        attempted_neighbors
    )

    if next_hop is None:
        print("REROUTING FAILED: No more valid routes.")
        return

    name, info = next_hop

    # Prepare token for forwarding.
    token["hops"] += 1
    token["ttl"] -= 1

    payload = (json.dumps(token) + "\n").encode("utf-8")

    # Try connecting to the selected neighbor.
    for attempt in range(1, 6):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.settimeout(4)
                client.connect((info["ip_addr"], info["port"]))
                client.sendall(payload)

            print(f"FORWARDED to {name}")
            return

        except OSError as error:
            print(f"Attempt {attempt}/5 failed: {error}")
            time.sleep(2)

    print(f"BROKEN LINK: Could not reach {name}.")

    # Remember that this neighbor failed.
    attempted_neighbors.add(name)

    print("Searching for another valid route...")

    # Try another neighbor.
    send_token(token, attempted_neighbors)
     
def process_token(token):    
    print("\nTOKEN RECEIVED")
    print("Message:", token["message"])
    print("Route so far:", " -> ".join(token["path"]))
    
    # CHeck if this node is the destination
    if token["destination"] == MY_NAME:
       print("\n*** DESTINATION REACHED! ***")
       print("Message:", token["message"])
       print("Route:", " -> ".join(token["path"]))
       print("File/message successfully delivered!")
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
            conn, addr = server.accept()
            # Store the connected socket in conn and the address in addr.

            with conn:
                try:
                    token = receive_json(conn)
                    if token is not None:
                        process_token(token)
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
                    print("Bad token received:", error)

def create_new_token(message, destination):
    return {
        "token_id": uuid.uuid4().hex[:8],
        "origin": MY_NAME,
        "message": message,
        "destination": destination,
        "path": [MY_NAME],
        "stamps": [MY_STAMP],
        "hops": 0,
        "ttl": MAX_HOPS,
        "started_at": time.time()
    }

listener = threading.Thread(target=listen_forever, daemon=True)

receiver_thread = threading.Thread(
    target=listen_for_heartbeats,
    daemon=True
)
monitoring_thread= threading.Thread(target = monitor_neighbors, daemon=True)

sender_thread = threading.Thread(
    target=send_heartbeats,
    daemon=True
)

listener.start()
ready_event.wait()
receiver_thread.start()
sender_thread.start()
monitoring_thread.start()


print("\nYour node is ready.")
print("Do not send until the instructor says GO.")

while True:
    command = input("\nType SEND to start a token, or QUIT: ").strip().upper()

    if command == "SEND":
        message = input("Message to send: ").strip()
        destination = input("Enter destination node: ").strip()
        
        if message and destination:
            send_token(create_new_token(message,destination))
        else:
            print("Message and destination cannot be empty.")

    elif command == "QUIT":
        print("Closing node.")
        break

    else:
        print("Please type SEND or QUIT.")
