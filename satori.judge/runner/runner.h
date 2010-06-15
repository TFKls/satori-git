#include <csignal>
#include <ctime>
#include <map>
#include <set>
#include <string>
#include <vector>

#include <sys/resource.h>
#include <sys/time.h>
#include <sys/types.h>

class Runner
{
  private:
    static int child_runner(void*);
    static std::map<long, Runner*> runners;
    class Initializer
    {
      private:
        static void signalhandler(int, siginfo_t*, void*);
        static std::vector<int> signals;
        static std::vector<struct sigaction> handlers;
      public:
        Initializer();
        static void Stop();
    };
    class ProcStat
    {
      public:
        int pid,ppid,pgrp,sid,tty,tpgid,exit_signal,cpu_number;
        unsigned int flags,sched_priority,sched_policy;
        long cutime,cstime,priority,nice,threads,alarm,rss;
        unsigned long minflt,cminflt,majflt,cmajflt,utime,stime,vsize,rss_lim,start_code,end_code,start_stack,esp,eip,signal,blocked,sig_ignore,sig_catch,wchan,nswap,cnswap,guest_time,cguest_time;
        unsigned long long start_time,io_delay;
        char state;
        std::string command;
        int mem_size, mem_resident, mem_shared, mem_text, mem_lib, mem_data, mem_dirty;
        ProcStat(int, Runner*);
    };
    class UserStat
    {
      private:
        void set(void*);
      public:
        bool ok;
        std::string name;
        std::string password;
        long uid;
        long gid;
        std::string gecos;
        std::string dir;
        std::string shell;
        UserStat(const std::string&);
        UserStat(long);
    };
    class GroupStat
    {
      private:
        void set(void*);
      public:
        bool ok;
        std::string name;
        std::string password;
        long gid;
        std::vector<std::string> members;
        GroupStat(const std::string&);
        GroupStat(long);
    };
    static Initializer initializer;
    int  debfd;
    void debug(const char*, ...);
    void fail(const char*, ...);
    void set_rlimit(const std::string&, int, long);
    void drop_capabilities();
    void drop_capability(const std::string&, int);
    static bool milisleep(long);
    static long miliseconds(const timeval&);
    static long miliseconds(const timespec&);
    static std::pair<long, long> miliseconds(const rusage&);
    static std::pair<long, long> miliseconds(const ProcStat&);
    bool parse_yaml(const std::string&, std::map<std::string, std::string>&);
    bool dump_yaml(const std::map<std::string, std::string>&, std::string&);
    bool contact_controller(std::string, const std::map<std::string, std::string>&, std::map<std::string, std::string>&);
    bool check_times();
    void run_child();
    void run_parent();
    void process_child();
    int  pipefd[2];
    long child;
    std::set<long> offspring;
    bool after_exec;
    long start_time;
    std::pair<long, long> before_exec_time;
    std::pair<long, long> dead_pids_time;
    long inside_syscall;

  public:
    // File to put debug
    std::string debug_file;
    // Directory to chroot into
    std::string dir;
    bool pivot;
    // Executable to run (inside chroot)
    std::string exec;
    // Executable working dir (inside chroot)
    std::string work_dir;
    // Parameters
    std::vector<std::string> params;
    // User settings
    std::string user;
    std::string group;
    // Ptrace?
    bool ptrace;
    bool ptrace_safe;
    // Environment
    enum ENV_LEVEL
    {
      ENV_EMPTY,
      ENV_SIMPLE,
      ENV_FULL,
      ENV_COPY
    };
    ENV_LEVEL env_level;
    enum CAP_LEVEL
    {
      CAP_EMPTY,
      CAP_SAFE,
      CAP_COPY,
      CAP_FULL
    };
    CAP_LEVEL cap_level;
    std::map<std::string, std::string> env_add;
    std::set<std::string> env_del;
    // Memory limits (in bytes)
    long memory_space;
    long stack_space;
    long data_space;
    // Time limits (in miliseconds)
    long cpu_time;
    long user_time;
    long system_time;
    long real_time;
    // FS limits
    long descriptor_count;
    long file_size;
    long sum_write;
    long sum_read;
    std::vector<std::string> read_files;
    std::vector<std::string> write_files;
    // Threading limits
    long thread_count;
    // Scheduling
    long priority; // the bigger, the better (0 = 19, 39 = -20)
    std::set<int> scheduler_cpu;
    int  scheduler_policy; // SCHED_FIFO, SCHED_RR, SCHED_OTHER, SCHED_BATCH, SCHED_IDLE
    int  scheduler_priority; // the bigger, the better
    // Redirects (outside chroot!)
    std::string input;
    std::string output;
    long output_size; // in bytes
    bool output_trunc;
    std::string error;
    long error_size; // in bytes
    bool error_trunc;
    bool error_to_output;
    // Flags
    bool lock_memory;
    bool collect_read_write_files;
    bool new_ipc;
    bool new_net;
    bool new_mount;
    bool new_pid;
    bool new_uts;
    bool search_path;
    std::string controller_host;
    int controller_port;
    Runner()
      : debfd(-1)
      , child(-1)
      , offspring()
      , after_exec(false)
      , start_time(0)
      , before_exec_time(0,0)
      , dead_pids_time(0,0)
      , debug_file("")
      , dir("")
      , pivot(false)
      , exec("")
      , work_dir("/")
      , params()
      , user("")
      , group("")
      , ptrace(false)
      , ptrace_safe(false)
      , env_level(ENV_COPY)
      , cap_level(CAP_FULL)
      , env_add()
      , env_del()
      , memory_space(-1)
      , stack_space(-1)
      , data_space(-1)
      , cpu_time(-1)
      , user_time(-1)
      , system_time(-1)
      , real_time(-1)
      , descriptor_count(-1)
      , file_size(-1)
      , sum_write(-1)
      , sum_read(-1)
      , read_files()
      , write_files()
      , thread_count(-1)
      , priority(-1)
      , scheduler_cpu()
      , scheduler_policy(-1)
      , scheduler_priority(0)
      , input("")
      , output("")
      , output_size(-1)
      , output_trunc(false)
      , error("")
      , error_size(-1)
      , error_trunc(false)
      , error_to_output(false)
      , lock_memory(false)
      , collect_read_write_files(false)
      , new_ipc(false)
      , new_net(false)
      , new_mount(false)
      , new_pid(false)
      , new_uts(false)
      , search_path(false)
      , controller_host("")
      , controller_port(-1)
    {}
    ~Runner();

    void Run();
    void Stop();
    void Wait();

    enum RES_STATUS
    {
      RES_OK,
      RES_TIME,
      RES_MEMORY,
      RES_IO,
      RES_ILLEGAL,
      RES_RUNTIME,
      RES_STOP,
      RES_FAIL,
      RES_OTHER
    };
    struct Result
    {
      RES_STATUS status;
      int    exit_status;
      rusage usage;
      unsigned long memory;
      unsigned long cpu_time;
      unsigned long user_time;
      unsigned long system_time;
      unsigned long real_time;
      unsigned long sum_write;
      unsigned long sum_read;
      std::set<std::string> read_files;
      std::set<std::string> write_files;

      Result()
        : status(RES_OTHER)
        , exit_status(0)
        , memory(0)
        , cpu_time(0)
        , user_time(0)
        , system_time(0)
        , real_time(0)
        , sum_write(0)
        , sum_read(0)
      {}
    };
    
    Result result;
};
