// dpi_py.c
#define _POSIX_C_SOURCE 200112L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
#include <sys/socket.h>

static int sock_fd = -1;

static int connect_to_server(const char *ip, int port) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port   = htons((uint16_t)port);
    if (inet_pton(AF_INET, ip, &addr.sin_addr) != 1) {
        close(fd);
        return -1;
    }

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

// DPI: int py_init(string ip, int port);
int py_init(const char *ip, int port) {
    if (sock_fd >= 0) return 0;
    sock_fd = connect_to_server(ip, port);
    if (sock_fd < 0) {
        fprintf(stderr, "py_init: connect failed (%s)\n", strerror(errno));
        return -1;
    }
    return 0;
}

static int recv_line(char *out, size_t out_sz) {
    size_t n = 0;
    while (n + 1 < out_sz) {
        char c;
        ssize_t r = recv(sock_fd, &c, 1, 0);
        if (r <= 0) return -1;
        if (c == '\n') break;
        out[n++] = c;
    }
    out[n] = '\0';
    return 0;
}

// DPI: int unsigned py_get(int cycle);
uint32_t py_get(int cycle) {
    if (sock_fd < 0) return 0;

    char req[64];
    snprintf(req, sizeof(req), "GET %d\n", cycle);

    ssize_t w = send(sock_fd, req, strlen(req), 0);
    if (w < 0) return 0;

    char line[128];
    if (recv_line(line, sizeof(line)) != 0) return 0;

    // Parse returned integer
    uint32_t val = (uint32_t)strtoul(line, NULL, 10);
    return val;
}

// DPI: void py_close();
void py_close(void) {
    if (sock_fd < 0) return;
    const char *q = "QUIT\n";
    (void)send(sock_fd, q, strlen(q), 0);

    char line[128];
    (void)recv_line(line, sizeof(line)); // ignore
    close(sock_fd);
    sock_fd = -1;
}
