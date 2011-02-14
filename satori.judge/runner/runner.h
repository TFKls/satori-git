// vim:ts=4:sts=4:sw=4:expandtab
#include <csignal>
#include <ctime>
#include <map>
#include <queue>
#include <set>
#include <string>
#include <vector>

#include <sys/resource.h>
#include <semaphore.h>
#include <sys/time.h>
#include <sys/types.h>

class Runner
{
    private:
        static std::map<int, Runner*> runners;

        static bool sigterm;
        static bool sigalarm;

        static void Register(int, Runner*);
        static void Unregister(int);
        static void Process();
        static void ProcessLoop(long);

        class Initializer
        {
            private:
                static void SignalHandler(int, siginfo_t*, void*);
                static std::vector<struct sigaction> handlers;
            public:
                static std::vector<int> signals;
                static std::set<int> debug_fds;
                Initializer();
                static void Stop();
                static void Debug(const char*, va_list);
                static void Fail(int, const char*, va_list);
        };
        static Initializer initializer;
        static void Debug(const char*, ...);
        static void Fail(const char*, ...);

        class Buffer
        {
            private:
                char* buf;
                size_t size;
                size_t fill;
            public:
                Buffer(size_t =0);
                ~Buffer();
                void Append(void*, size_t);
                std::string String() const;
                static int YamlWriteCallback(void*, unsigned char*, size_t);
                static size_t CurlWriteCallback(void*, size_t, size_t, void*);
        };

        class ProcStats
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
                ProcStats(int);
        };

        class UserInfo
        {
            private:
                void set(void*);
            public:
                bool ok;
                std::string name;
                std::string password;
                int uid;
                int gid;
                std::string gecos;
                std::string dir;
                std::string shell;
                UserInfo(const std::string&);
                UserInfo(int);
        };

        class GroupInfo
        {
            private:
                void set(void*);
            public:
                bool ok;
                std::string name;
                std::string password;
                int gid;
                std::vector<std::string> members;
                GroupInfo(const std::string&);
                GroupInfo(int);
        };

        class MountsInfo
        {
            private:
                struct Mount
                {
                    std::string source;
                    std::string target;
                    std::string type;
                    std::string options;
                    Mount(std::string _source = "", std::string _target = "", std::string _type = "", std::string _options = "")
                        : source(_source)
                        , target(_target)
                        , type(_type)
                        , options(_options)
                    {
                    }
                };
            public:
                std::vector<Mount> mounts;
                std::map<std::string, Mount> targets;
                MountsInfo();
                static bool Available();
        };

        class Controller
        {
            private:
                std::string host;
                int port;
                static bool Parse(const std::string&, std::map<std::string, std::string>&);
                static bool Dump(const std::map<std::string, std::string>&, std::string&);
                bool Contact(const std::string&, const std::map<std::string, std::string>&, std::map<std::string, std::string>&);
                static void CheckOK(const std::string&, const std::map<std::string, std::string>&);
            public:
                Controller(const std::string&, int);
                void GroupCreate(const std::string&);
                void GroupJoin(const std::string&);
                void GroupDestroy(const std::string&);
                struct Limits
                {
                    long memory;
                    Limits()
                        : memory(-1)
                    {
                    }
                };
                void GroupLimits(const std::string&, const Limits&);
                struct Stats
                {
                    long utime, stime, memory;
                    Stats()
                        : utime(0)
                        , stime(0)
                        , memory(0)
                    {
                    }
                };
                Stats GroupStats(const std::string&);
        };
        Controller* controller;

        void set_rlimit(const std::string&, int, long);
        void drop_capabilities();
        void drop_capability(const std::string&, int);
        static bool milisleep(long);
        static long miliseconds(const timeval&);
        static long miliseconds(const timespec&);
        static void ms_timeval(long, timeval&);
        static void ms_timespec(long, timespec&);
        static std::pair<long, long> miliseconds(const rusage&);
        static std::pair<long, long> miliseconds(const ProcStats&);
        static std::pair<long, long> miliseconds(const Controller::Stats&);
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
        bool mount_proc;
        bool new_pid;
        bool new_uts;
        bool search_path;
        std::string controller_host;
        int controller_port;
        std::string cgroup;
        long cgroup_memory;
        long cgroup_time;
        long cgroup_user_time;
        long cgroup_system_time;


        Runner()
            : controller(NULL)
            , child(-1)
            , parent(-1)
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
            , mount_proc(false)
            , new_pid(false)
            , new_uts(false)
            , search_path(false)
            , controller_host("")
            , controller_port(-1)
            , cgroup("")
            , cgroup_memory(-1)
            , cgroup_time(-1)
            , cgroup_user_time(-1)
            , cgroup_system_time(-1)
        {}
        ~Runner();

        void Run();
        void Stop();
        bool Check();
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
            unsigned long cgroup_memory;
            unsigned long cgroup_time;
            unsigned long cgroup_user_time;
            unsigned long cgroup_system_time;
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
                , cgroup_memory(0)
                , cgroup_time(0)
                , cgroup_user_time(0)
                , cgroup_system_time(0)
            {}
            void SetStatus(RES_STATUS _status)
            {
                if (status == RES_OTHER)
                    status = _status;
            }
        };

        Result result;
};
