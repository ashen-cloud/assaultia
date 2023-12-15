#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>

int main() {
    pid_t pid = getpid();
    
    printf("PID: %d\n", pid);
    
    int value = 1337;

    printf("Address: %p\n", &value);

    while (1) {
        value++;
        
        printf("Value: %d\n", value);

        fflush(stdout);
        
        usleep(1000 * 1000); // 1000 ms = 1000 * 1000 us
    }
    
    return 0;
}
