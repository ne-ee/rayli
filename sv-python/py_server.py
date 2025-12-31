#!/usr/bin/env python3
import socket
import threading

HOST = "127.0.0.1"
PORT = 50007

def gen_sample(cycle: int) -> int:
    # Replace this with your real generator.
    # Example: deterministic pseudo “stimulus”
    return (cycle * 3 + 7) & 0xFFFFFFFF

def handle_client(conn: socket.socket, addr):
    try:
        buf = b""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                cmd = parts[0].upper() if parts else b""

                if cmd == b"GET" and len(parts) == 2:
                    cycle = int(parts[1])
                    val = gen_sample(cycle)
                    conn.sendall(f"{val}\n".encode("ascii"))
                elif cmd == b"QUIT":
                    conn.sendall(b"OK\n")
                    return
                else:
                    conn.sendall(b"ERR\n")
    finally:
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Python server listening on {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    main()
