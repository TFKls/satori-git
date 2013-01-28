#include <cstdio>
#include <cstdlib>
#include <cassert>
#include <cstring>
#include <algorithm>
#include <climits>
#include <vector>
#include <string>
#include <set>
using namespace std;

char command[256];
char file_1[50];
char file_2[50];
char path[50];

//1 - first file, 2 - second file, 3 - block size
int main(int argc, char **argv){
    assert(argc == 4);

    strcpy(file_1, argv[1]);

    strcpy(file_2, argv[2]);

    strcpy(path, "tmp/");


    //:
    sprintf(command, "grep -e \"^[ \\t]*#\" %s%s > temp/inc1.cpp", path, file_1);


    //Run that command:
    system(command);


    //:
    sprintf(command, "grep -e \"^[ \\t]*#\" %s%s > temp/inc2.cpp", path, file_2);

    //Run that command:
    system(command);

    //:
    sprintf(command, "./parseClang temp/inc1.cpp > temp/inc1.pre");

    //Run that command:
    system(command);


    //:
    sprintf(command, "./parseClang temp/inc2.cpp > temp/inc2.pre");

    //Run that command:
    system(command);


    //Prepare system command to run prepr02 on created path to i sorcecode:
    sprintf(command, "./parseClang %s%s > temp/%s.pre", path, file_1, file_1);

    //Run that command:
    system(command);


    //Prepare system command to run prepr02 on created path to i sorcecode:
    sprintf(command, "./parseClang %s%s > temp/%s.pre", path, file_2, file_2);

    //Run that command:
    system(command);

    //:
    sprintf(command, "dd if=temp/%s.pre bs=1 skip=`stat -c %s temp/inc1.pre` of=temp/%s.prex", file_1,"%s", file_1);


    //Run that command:
    system(command);

    //:
    sprintf(command, "dd if=temp/%s.pre bs=1 skip=`stat -c %s temp/inc2.pre` of=temp/%s.prex", file_2,"%s", file_2);

    //Run that command:
    system(command);


    int min_block = 10;
 
    sscanf(argv[3], "%d", &min_block);

    //Prepare system command to run compare03 on submits V[i] and V[j] with min_block:
    sprintf(command, "./compare03 temp/%s.prex temp/%s.prex %d > stuff.res", file_1, file_2, min_block);

    //execute shell command with mode 'r' for reading:
    system(command);



}
