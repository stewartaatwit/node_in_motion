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
        "last_seen": None
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
        )
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
               print("LAST SEEN:", neighbors[sender_name]["last_seen"])
               print("STATUS:", neighbors[sender_name]["status"])
               print(f"{sender_name} is alive")
               print(
                   f"Heartbeat received from "
                   f"{sender_name} ({sender_ip})"
                   
                )
               
                            

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
def get_next_hop():
    """Choose the primary neighbor first, then an available neighbor."""

    with routing_table_lock:

        routes = list(routing_table.items())

        # Find the primary neighbor.
        primary = [
            (name, info) for name, info in routes
            if info["is_primary"]
        ]

        # Find other neighbors that are alive.
        backups = [
            (name, info) for name, info in routes
            if info["status"] == "alive"
            and not info["is_primary"]
        ]

        # Try the primary unless it is known to be unavailable.
        if primary and primary[0][1]["status"] != "unavailable":
            return primary[0]

        # Otherwise, choose an available backup.
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
        
        if name in neighbors:
                neighbors[name]["status"] = "alive"
                neighbors[name]["last_seen"]= time.time()
    with routing_table_lock:
        if name in routing_table:
                routing_table[name]["status"]= "alive"
                routing_table[name]["last_seen"]= time.time()
                
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

def send_token(token):
    if token["ttl"] <= 0:
        print("STOPPED: TTL reached zero. The ring may be configured incorrectly.")
        return

    token["hops"] += 1
    token["ttl"] -= 1
    payload = (json.dumps(token) + "\n").encode("utf-8")

    # Get the next available neighbor
    next_hop = get_next_hop()
    
    if next_hop is None:
        print("REROUTING FAILED: No available neighbors.")
        return
    
        # Create a list of possible routes.
    with routing_table_lock:
    
        routes = list(routing_table.items())
    
            # Start with the selected route.
        candidates = [next_hop]
    
            # Add all other alive neighbors as backup routes.
        for name, info in routes:
            
            if (
                name != next_hop[0]
                and info["status"] == "alive"
               
            ):
                candidates.append((name, info))
    
    # Try each available neighbor.
    for name, info in candidates:
    
        for attempt in range(1, 6):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                    client.settimeout(4)
    
                    # TODO 1: Connect to an available neighbor.
                    client.connect((info["ip_addr"], info["port"]))
                    
                    # TODO 2: Send the entire payload.
                    client.sendall(payload)
                    
                if name == next_hop[0]:
                    print(f"FORWARDED to {name}")
                else:
                    print(f"REROUTED successfully to {name}")
    
               # print(f"FORWARDED to {NEXT_IP}:{NEXT_PORT}")
                return
    
            except OSError as error:
                print(f"Attempt {attempt}/5 failed: {error}")           
                time.sleep(2)
    
        print("BROKEN LINK: Could not reach the next student after 5 attempts.")
    
     # Mark the failed neighbor unavailable.
      #Commented out for now becauise a failed TCP connection does not necessarily
      # mean that the node is deadmark_neighbor_unavailable(name)
       
        print("Searching for another route...")
       
    print("BROKEN LINK: No available routes found.")
    
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
            conn, addr = server.accept()
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
