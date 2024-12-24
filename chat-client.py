import socket
import sys
import threading

def handle_messages(conn: socket.socket):
    """A function to receive incoming messages to the `conn` socket and print to terminal. To be used in a thread."""
    while True:
        try:
            msg = conn.recv(1024)
            if msg:
                print("\r" + msg.decode() + "\nme> ", end = "")
            else:
                conn.close()
                break

        except Exception as e:
            print(f"Error handling message from server: {e}")
            conn.close()
            break

def main() -> None:
    if len(sys.argv) < 3:
        print(f"Error: you must specify the host and the port, e.g. 'py {sys.argv[0]} 127.0.0.1 65432' for localhost.")
        return

    host, port = sys.argv[1], int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print("Trying to connect...")
        s.connect((host, port)) 
        print("Connected!")
        # create separate thread to handle incoming messages, while this main function handles the user sending messages.
        threading.Thread(target = handle_messages, args = [s]).start()

        while True:
            msg = input("me> ")
            if msg == "end":
                print("Leaving chat...")
                s.close()
                break
            else:
                s.sendall(msg.encode())
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    main()