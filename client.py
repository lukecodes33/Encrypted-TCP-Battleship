#!/usr/bin/env python3
import socket
import sys
import time
import ssl

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        print("Error: Port must be an integer.")
        sys.exit(1)

    # Create a TCP socket using the port and local host parsed from startClient script 
    # Automatically sends a Start Game message to the server
    # Create a raw TCP socket
    # Wrap socket in TLS context using the server certificate
    # Check for host name needs to be local host for this instance
    # Loads the server.crt created in the directory, verifys the servers identity and then encrypts the tunnel with TLS
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as raw_sock:
        
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.check_hostname = True  
        ctx.load_verify_locations("server.crt")  
        sock = ctx.wrap_socket(raw_sock, server_hostname=host)

        try:
            sock.connect((host, port))
        except ConnectionRefusedError:
            print(f"Error: Could not connect to {host}:{port}")
            sys.exit(1)
        print(f"Connected to {host}:{port}")

        sock.sendall("Start game".encode('utf-8'))
        response = sock.recv(4096)
        responseText = response.decode('utf-8').strip()
        print("")
        print(responseText)
        print("")

        while True:
            #Begins a loop of prompting co ordinatesm, checking to make sure they are valid board locations
            while True:
                message = input("Enter Co-ordinates (A1 to I9): ").strip()
                if len(message) == 2:
                    letter = message[0].upper()
                    digit = message[1]
                    if letter in "ABCDEFGHI" and digit in "123456789":
                        break
                print("Invalid coordinate. Please enter a coordinate from A1 to I9.")

            #Once co ordinates are confirmed as valid, encodes the messages and sends it to the server.
            #Time.sleep is used to remove the instantanous messaging ability and double messaging the server and becoming stuck

            time.sleep(0.5)
            # Send the message to the server
            sock.sendall(message.encode('utf-8'))

            # Wait for the server's response (up to 4096 bytes)
            # Displays the servers message and prints empty lines for spacing. This will display the board after each shot
            response = sock.recv(4096)

            responseText = response.decode('utf-8').strip()
            print("")
            print(responseText)
            print("")

            # Once server prompts that user has sunk all its battleships, gives a congraulations message and drops the connection,
            
            if "YOU SUNK MY BATTLESHIPS" in responseText:
                 print("Congratulations, you have won the game. Re connect to play again!")
                 time.sleep(5)
                 sys.exit()     

if __name__ == "__main__":
    main()