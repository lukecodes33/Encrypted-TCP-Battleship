#!/bin/bash

import ssl
import socket
import sys
import time
import random

def createEmptyBoard():
    # Creates a 9x9 board filled with dots ('.')
    return [["." for _ in range(9)] for _ in range(9)]


def placeAllShips(board):
    # Place all required ships onto the board.
    # Define ships as tuples: (symbol, length)
    ships = [("L", 3), ("H", 4), ("A", 2), ("C", 5)]
    
    for symbol, length in ships:
        placeShips(board, length, symbol)


def placeShips(board, length, symbol):
    # Randomly places a ship of the given length and symbol on the board. Checks to make sure the ship can be placed within array boundaries
    placed = False
    while not placed:
        orientation = random.choice(["horizontal", "vertical"])
        if orientation == "horizontal":
            row = random.randint(0, 8)
            col = random.randint(0, 9 - length)  
        else:  
            row = random.randint(0, 9 - length)  
            col = random.randint(0, 8)
        
        if canPlaceShips(board, row, col, length, orientation):
            # Place the ship by filling the board cells with the ship's symbol
            if orientation == "horizontal":
                for i in range(length):
                    board[row][col + i] = symbol
            else:
                for i in range(length):
                    board[row + i][col] = symbol
            placed = True


def canPlaceShips(board, row, col, length, orientation):
    #Checks if a ship can be placed at (row, col) with the given length and orientation.
    if orientation == "horizontal":
        if col + length > 9:
            return False
        return all(board[row][col + i] == "." for i in range(length))
    else: 
        if row + length > 9:
            return False
        return all(board[row + i][col] == "." for i in range(length))


def printBoard(board):
    # Used to print the client side board with row and column labels to track progress
    columns = list("ABCDEFGHI")
    board_str = "  " + " ".join(columns) + "\n"
    for i, row in enumerate(board):
        board_str += f"{i+1} " + " ".join(row) + "\n"
    return board_str



def cellToCoordinate(cell):
    
    # Converts a cell coordinate (e.g., "A1", "B3", "I9") into a list [row, col],
    # where row and col are zero-indexed. For example, "A1" -> [0, 0] and "I9" -> [8, 8].

    if len(cell) < 2 or len(cell) > 3:
        return None  

    cell = str(cell) 
    col_letter = cell[0].upper()
    row_number = cell[1:]
    
    try:
        row = int(row_number) - 1  
    except ValueError:
        return None
    
    col = ord(col_letter) - ord('A')
    if 0 <= row < 9 and 0 <= col < 9:
        return [row, col]
    else:
        return None


def startServer(port):
    # Create a TCP socket and bind to port passed by startServer.sh
    # Throws error if port is currently in use

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(("", port))
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Start listening for incoming connections
    sock.listen(5)

    # Loads both server.crt and server.key
    # Upon connection of client, server presents the server.crt certificate to the client to prove authenticity
    # If client validates that, the handshake is made and the tunnel is wrapped in TLS
    # If it is rejected, the connection is dropped and the handshake fails
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(certfile="server.crt", keyfile="server.key")

    while True:
        client_sock, addr = sock.accept()

        try:
           conn = ctx.wrap_socket(client_sock, server_side=True)
        except ssl.SSLError as err:
            print("TLS handshake failed:", err)
            client_sock.close()
            continue

        print(f"{addr} connected to server")

        data = conn.recv(4096)

        # Decode the received bytes to a string and strip whitespace/newlines
        message = data.decode('utf-8').strip()
        time.sleep(0.5)

        #Begins game and creates instance of server and client board
        if message.upper() == "START GAME":
             
            serverBoard = createEmptyBoard()
            placeAllShips(serverBoard)
            shotsTaken = 0

            clientBoard = createEmptyBoard()
            currentClientBoard = printBoard(clientBoard)

            seedInt = random.randint(1, 9_999_999)
            seed = str(seedInt)
            shipsInPosition = "SHIPS IN POSITION\n" + currentClientBoard + "\n\n" + "Seed:" + seed
            conn.sendall(shipsInPosition.encode('utf-8'))

            while True:

                data = conn.recv(4096)
                message = data.decode('utf-8').strip()
                time.sleep(0.5)

                location = cellToCoordinate(message)

                if location is not None:
                    shotsTaken += 1
                    row, col = location
                    serverBoardValue = serverBoard[row][col]

                    if serverBoardValue != '.':
                        # Update the client board and server board with an 'O'
                        clientBoard[row][col] = 'o'
                        serverBoard[row][col] = 'o'

                        updatedBoard = printBoard(clientBoard)


                        if all(cell in ['.', 'o'] for row in serverBoard for cell in row):
                            winningMessage = "YOU SUNK MY BATTLESHIPS in " + str(shotsTaken) + " shots!\n" + "Seed:" + seed
                            conn.sendall(winningMessage.encode('utf-8'))
                            print(f"{addr} won the game, dropping connection")
                            conn.close()  
                            break 


                        messageToClient = "Hit! Board updated.\n" + updatedBoard
                        conn.sendall(messageToClient.encode('utf-8'))


                    else:
                        clientBoard[row][col] = 'x'
                        updatedBoard = printBoard(clientBoard)
                        messageToClient = "Miss! Board updated.\n" + updatedBoard
                        conn.sendall(messageToClient.encode('utf-8'))

                else:
                    conn.close()

try:
        port = int(sys.argv[1]) 
        print(f"Hosting on port: {port}")   
except ValueError:
        print("Error: Port must be an integer")
        sys.exit(1)

startServer(port)