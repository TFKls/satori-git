// vim:ts=4:sts=4:sw=4:expandtab
#include <csignal>
#include <ctime>
#include <map>
#include <memory>
#include <queue>
#include <set>
#include <string>
#include <vector>

#include <sys/resource.h>
#include <semaphore.h>
#include <sys/time.h>
#include <sys/types.h>

namespace runner {

    class Initializer {
        private:
        static void SignalHandler(int, siginfo_t*, void*);
        static std::vector<struct sigaction> handlers;
        static bool sigterm;
        static bool sigalarm;
        static void Process();
        public:
        static std::vector<int> signals;
        Initializer();
        static void Stop();
        static void ProcessLoop(double s);
    };

    class Logger {
        public:
        static sem_t semaphore;
        static std::set<int> debug_fds;
        enum Level { DEBUG, WARNING, ERROR, CRITICAL, NONE };
        private:
        static Level level;
        static void Print(const char*, va_list);
        public:
        static void SetLevel(Level);
        static void Debug(const char*, va_list);
        static void Warning(const char*, va_list);
        static void Error(const char*, va_list);
        static void Fail(int, const char*, va_list);
        Logger();
    };

    class Buffer {
        private:
        char* buf;
        size_t size;
        size_t fill;
        public:
        Buffer(size_t =0);
        ~Buffer();
        void Append(void*, size_t);
        std::string String() const;
        static size_t CurlWriteCallback(void*, size_t, size_t, void*);
    };

    class ProcStats {
        public:
        int pid,ppid,pgrp,sid,tty,tpgid,exit_signal,cpu_number;
        unsigned int flags,sched_priority,sched_policy;
        long cutime,cstime,priority,nice,threads,alarm,rss;
        unsigned long minflt,cminflt,majflt,cmajflt,utime,stime,vsize,rss_lim,start_code,end_code,start_stack,esp,eip,signal,blocked,sig_ignore,sig_catch,wchan,nswap,cnswap,guest_time,cguest_time;
        unsigned long long start_time,io_delay;
        char state;
        std::string command;
        unsigned long long mem_size, mem_resident, mem_shared, mem_text, mem_lib, mem_data, mem_dirty; // in bytes
        ProcStats(pid_t);
    };

    class UserInfo {
        public:
        bool ok;
        std::string name;
        std::string password;
        uid_t uid;
        gid_t gid;
        std::string gecos;
        std::string dir;
        std::string shell;
        UserInfo(std::string);
        UserInfo(uid_t);
        UserInfo();
    };

    class GroupInfo {
        public:
        bool ok;
        std::string name;
        std::string password;
        gid_t gid;
        std::vector<std::string> members;
        GroupInfo(std::string);
        GroupInfo(gid_t);
        GroupInfo();
    };

    class MountsInfo {
        private:
        struct Mount {
            std::string source;
            std::string target;
            std::string type;
            std::string options;
            Mount(std::string source = "", std::string target = "", std::string type = "", std::string options = "")
                : source(source)
                , target(target)
                , type(type)
                , options(options) {}
        };
        public:
        std::vector<Mount> mounts;
        std::map<std::string, Mount> targets;
        MountsInfo();
        static bool Available();
    };

    class Controller {
        private:
        std::string host;
        std::string session;
        std::string secret;
        std::string group;
        int port;
        static bool Parse(const std::string&, std::map<std::string, std::string>&);
        static bool Dump(const std::map<std::string, std::string>&, std::string&);
        bool Contact(const std::string&, const std::map<std::string, std::string>&, std::map<std::string, std::string>&);
        static void CheckOK(const std::string&, const std::map<std::string, std::string>&);
        public:
        Controller(std::string ="localhost", int =8765, std::string ="", std::string ="", std::string ="");
        void Attach();
        struct Limits {
            long long memory;
            long cpus;
            Limits(long long memory =0, long cpus =0)
                : memory(memory)
                , cpus(cpus) {}
        };
        void Limit(const Limits&);
        struct Stats {
            long time, utime, stime;
            long long memory;
            Stats()
                : time(0)
                , utime(0)
                , stime(0)
                , memory(0) {}
        };
        Stats Query();
        void Kill();
        void Close();
    };

    class PerfCounters {
        private:
        int fd_instructions;
        int fd_cycles;
        public:
        struct Stats {
            unsigned long instructions;
            unsigned long cycles;
            Stats()
                : instructions(0)
                , cycles(0) {}
        };
        PerfCounters(pid_t);
        ~PerfCounters();
        Stats PerfStats();
    };

    struct Result {
        enum RES_STATUS {
            RES_OK, RES_TIME, RES_MEMORY,
            RES_RUNTIME, RES_STOP, RES_FAIL,
            RES_OTHER
        };
        RES_STATUS status;
        int    exit_status;
        unsigned long long memory; // bytes
        double cpu_time; // seconds
        double user_time;
        double system_time;
        double real_time;
        unsigned long long cgroup_memory;
        double cgroup_time;
        double cgroup_user_time;
        double cgroup_system_time;
        unsigned long perf_instructions;
        unsigned long perf_cycles;

        Result()
            : status(RES_OTHER)
            , exit_status(0)
            , memory(0)
            , cpu_time(0)
            , user_time(0)
            , system_time(0)
            , real_time(0)
            , cgroup_memory(0)
            , cgroup_time(0)
            , cgroup_user_time(0)
            , cgroup_system_time(0)
            , perf_instructions(0)
            , perf_cycles(0) {}
        void SetStatus(RES_STATUS _status) {
            if (status == RES_OTHER)
                status = _status;
        }
    };

    void Debug(const char*, ...);
    void Warning(const char*, ...);
    void Fail(const char*, ...);

    int  total_write(int, const void*, size_t);
    int  total_read(int, void*, size_t);
    int  cat_open(const char*, int, int);
    void from_seconds(double, timeval&);
    void from_seconds(double, timespec&);
    double to_seconds(const timeval&);
    double to_seconds(const timespec&);
    struct CpuTimes {
        double user, system, time;
        CpuTimes(double user, double system)
            : user(user)
            , system(system)
            , time(user + system) {}
        CpuTimes(double user, double system, double time)
            : user(user)
            , system(system)
            , time(std::max(user + system, time)) {}
        CpuTimes(const rusage&);
        CpuTimes(const ProcStats&);
        CpuTimes(const Controller::Stats&);
        bool operator<= (const CpuTimes& o) const {
            return user <= o.user && system <= o.system && time <= o.time;
        }
        CpuTimes& operator+= (const CpuTimes& o) {
            user += o.user;
            system += o.system;
            time += o.time;
            return *this;
        }
    };

    class Runner
    {
        private:
        static std::map<int, Runner*> runners;
        static void Register(int, Runner*);
        static void Unregister(int);
        static Initializer initializer;
        static Logger logger;

        Controller* controller;

        void set_rlimit(const std::string&, int, long);
        void drop_capabilities();
        void drop_capability(const std::string&, int);
        static bool sleep(double);
        bool check_cgroup();
        bool check_times();
        static int child_runner(void*);
        void run_child();
        void run_parent();
        void process_child(long);
        int  pipefd[2];
        int  child;
        int  parent;
        std::set<int> offspring;
        bool after_exec;
        long start_time;
        CpuTimes dead_pids_time;
        long inside_syscall;
        std::unique_ptr<PerfCounters> perf;

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
        // Environment
        enum ENV_LEVEL {
            ENV_EMPTY,
            ENV_SIMPLE,
            ENV_FULL,
            ENV_COPY
        };
        ENV_LEVEL env_level;
        enum CAP_LEVEL {
            CAP_EMPTY,
            CAP_SAFE,
            CAP_COPY,
            CAP_FULL
        };
        CAP_LEVEL cap_level;
        std::map<std::string, std::string> env_add;
        std::set<std::string> env_del;
        // Memory limits (in bytes)
        long long memory_space;
        long long stack_space;
        long long data_space;
        // Time limits (in seconds)
        double cpu_time;
        double user_time;
        double system_time;
        double real_time;
        long long instructions;
        long long cycles;
        // FS limits
        long descriptor_count;
        // Scheduling
        long priority; // the bigger, the better (0 = 19, 39 = -20)
        // Redirects (outside chroot!)
        std::string input;
        std::string output;
        bool output_trunc;
        std::string error;
        bool error_trunc;
        bool error_to_output;
        // Flags
        bool lock_memory;
        bool new_ipc;
        bool new_net;
        bool new_mount;
        bool mount_proc;
        bool new_pid;
        bool new_uts;
        bool search_path;
        std::string control_host;
        int control_port;
        std::string control_session;
        std::string control_secret;
        std::string cgroup;
        long long cgroup_memory;
        double cgroup_time;
        double cgroup_user_time;
        double cgroup_system_time;
        long cgroup_cpus;

        Runner()
            : controller(NULL)
            , child(-1)
            , parent(-1)
            , offspring()
            , after_exec(false)
            , start_time(0)
            , dead_pids_time(0,0)
            , debug_file("")
            , dir("")
            , pivot(false)
            , exec("")
            , work_dir("")
            , params()
            , user("")
            , group("")
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
            , instructions(-1)
            , cycles(-1)
            , descriptor_count(-1)
            , priority(-1)
            , input("")
            , output("")
            , output_trunc(false)
            , error("")
            , error_trunc(false)
            , error_to_output(false)
            , lock_memory(false)
            , new_ipc(false)
            , new_net(false)
            , new_mount(false)
            , mount_proc(false)
            , new_pid(false)
            , new_uts(false)
            , search_path(false)
            , control_host("")
            , control_port(-1)
            , cgroup("")
            , cgroup_memory(-1)
            , cgroup_time(-1)
            , cgroup_user_time(-1)
            , cgroup_system_time(-1) {}
        ~Runner();

        void Run();
        void Stop();
        bool Check();
        void Wait();
        
        static void StopAll();
        static void CheckAll();
        static void ProcessAChild(pid_t);

        Result result;
    };
}
