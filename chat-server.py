import sys
import socket
import selectors
import types

sel = selectors.DefaultSelector()
clients = []
user_num = 0

def remove_client(sock: socket.socket, uname: str) -> None:
    sel.unregister(sock)
    sock.close()
    for i, client in enumerate(clients):
        if client.uname == uname:
            del clients[i]
            break

def broadcast_message(msg: bytes, sender: types.SimpleNamespace, show_sender: bool) -> None:
    """Broadcast the message in `msg' to all connected clients. Sender should be the `data' attributed associated with the client sending the message,
    and if show_sender is true, the message will show as 'uname> msg'."""    
    for client in clients:
        if client.uname == sender.uname:
            continue
        else:
            if show_sender:
                client.outb += (f"{sender.uname}> ").encode() + msg
            else:
                client.outb += msg

def accept_wrapper(sock: socket.socket) -> None:
    """Accept a user into the chat."""
    global user_num
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # inb and outb are input buffers and output buffers respectively
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", uname = "user" + str(user_num))
    user_num += 1
    clients.append(data)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE # we want to know if the client is ready for read *or* write
    sel.register(conn, events, data=data)
    broadcast_message(f"{data.uname} has entered the chat.".encode(), data, show_sender = False)

def service_connection(key: selectors.SelectorKey, mask: int) -> None:
    """If applicable, read from the socket and write to it, using the input and output buffers."""
    sock = key.fileobj
    data = key.data

    # if the socket is ready to be read from (presumably only triggered if it has sent sthg?)
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
            if recv_data:
                print(f"Received message: '{recv_data.decode()}' from {data.uname}. Broadcasting to all.")
                broadcast_message(recv_data, data, show_sender = True)
            else:
                print(f"Closing connection to {data.addr}")
                broadcast_message(f"{data.uname} has left the chat.".encode(), data, show_sender = False)
                remove_client(sock, data.uname)
        except Exception as e:
            print(f"Error receiving data from {data.uname}: {e}. Closing connection.")
            broadcast_message(f"{data.uname} has left the chat.".encode(), data, show_sender = False)
            remove_client(sock, data.uname)

    # if socket is ready to write to (which it always should be)
    if mask & selectors.EVENT_WRITE:
        # if there's anything in the outbuffer, send it back to the client
        if data.outb:
            # sock.send returns how many bytes have been sent
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

def main() -> None:
    if len(sys.argv) < 3:
        print(f"Error: you must specify the host and the port, e.g. 'py {sys.argv[0]} 127.0.0.1 65432' for localhost.")
        return
    
    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print(f"Listening on {(host, port)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    # event loop
    try:
        while True:
            # looks through the sockets and finds one that is ready for input/output
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # this is the listening socket and you need to accept the connection
                    accept_wrapper(key.fileobj)
                else:
                    # it's an existing connection and you need to do sthg with it
                    service_connection(key, mask)
    except KeyboardInterrupt:
        # this never seems to work, maybe blocked by sthg above
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

if __name__ == "__main__":
    main()
