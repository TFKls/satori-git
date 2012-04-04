// vim:ts=4:sts=4:sw=4:expandtab
#include <cassert>
#include <cerrno>
#include <cmath>
#include <csignal>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>

#include <algorithm>
#include <map>
#include <set>
#include <string>
#include <vector>

#include <fcntl.h>
#include <grp.h>
#include <pthread.h>
#include <pwd.h>
#include <sched.h>
#include <unistd.h>
#include <poll.h>

#include <sys/capability.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/user.h>
#include <sys/wait.h>

#include <linux/fs.h>
#include <linux/limits.h>

#include <asm/param.h>

#include <curl/curl.h>
#include <yaml.h>

#include "runner.h"

using namespace std;

namespace runner {

map<int, Runner*> Runner::runners;
bool Initializer::sigterm;
bool Initializer::sigalarm;
vector<int> Initializer::signals;
vector<struct sigaction> Initializer::handlers;
set<int> Logger::debug_fds;
Initializer Runner::initializer;
Logger Runner::logger;

Initializer::Initializer()
{
    sigterm = false;
    sigalarm = false;
    signals.push_back(SIGALRM);
    signals.push_back(SIGTERM);
    signals.push_back(SIGCHLD);
    handlers.resize(signals.size());
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_sigaction = &SignalHandler;
    action.sa_flags = SA_RESTART | SA_SIGINFO;
    sigfillset(&action.sa_mask);
    for (uint i=0; i<signals.size(); i++)
        sigaction(signals[i], &action, &handlers[i]);
}
void Initializer::Stop()
{
    for (uint i=0; i<signals.size(); i++)
        sigaction(signals[i], &handlers[i], NULL);
}
void Initializer::SignalHandler(int sig, siginfo_t* info, void* data)
{
    if (sig == SIGALRM)
        sigalarm = true;
    else if (sig == SIGTERM)
        sigterm = true;
}
void Runner::Register(int pid, Runner* runner)
{
    if(runners.find(pid) == runners.end())
    {
        runners[pid] = runner;
    }
    else
        Fail("Process %d was registered twice.\n", pid);
}
void Runner::Unregister(int pid)
{
    runners.erase(pid);
}
void Runner::StopAll()
{
	for (map<int, Runner*>::const_iterator i=runners.begin(); i!=runners.end(); i++)
		i->second->Stop();
}
void Runner::CheckAll()
{
	for (map<int, Runner*>::const_iterator i=runners.begin(); i!=runners.end(); i++)
		i->second->Check();
}
void Runner::ProcessAChild(pid_t pid)
{
	map<int, Runner*>::const_iterator i = runners.find(pid);
    if (i != runners.end())
        i->second->process_child(pid);
    else
    {
        ProcStats P(pid);
        i = runners.find(P.ppid);
        if (i != runners.end())
            i->second->process_child(pid);
        else
        {
            i = runners.find(P.pgrp);
            if (i != runners.end())
                i->second->process_child(pid);
            else
                waitpid(pid, NULL, 0);
        }
    }
}
	
void Initializer::Process()
{
    if (sigterm)
    {
        sigterm = false;
		Runner::StopAll();
    }
    if (sigalarm)
    {
        sigalarm = false;
		Runner::CheckAll();
    }
    siginfo_t info;
    while (1) {
        info.si_pid = 0;
        if (waitid(P_ALL, 0, &info, WEXITED | WSTOPPED | WNOHANG | WNOWAIT) < 0 && errno != ECHILD)
            Fail("waitid failed");
        if (info.si_pid == 0)
            break;
        int pid = info.si_pid;
		Runner::ProcessAChild(pid);
   }
}


void Initializer::ProcessLoop(long ms)
{
    timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    long to = miliseconds(ts)+ms;
    sigset_t orig_mask, blocked_mask;
    sigemptyset(&blocked_mask);
	for(vector<int>::iterator it = Initializer::signals.begin(); it != Initializer::signals.end(); ++it)
		sigaddset(&blocked_mask, *it);
    while (1) {
        sigprocmask(SIG_BLOCK, &blocked_mask, &orig_mask);
        Process();
        clock_gettime(CLOCK_REALTIME, &ts);
        long rem = to - miliseconds(ts);
        if (rem <= 0)
            break;
        ms_timespec(rem, ts);
        int res = ppoll(NULL, 0, &ts, &orig_mask);
        sigprocmask(SIG_SETMASK, &orig_mask, NULL);
        if (res < 0 && errno == EINTR) {
            Debug("ppoll interrupted");	
            continue;
        }
        if (res < 0)
            Fail("ppoll failed");
        if (res == 0)
            break;
    }
}       

Logger::Level Logger::level = Logger::ERROR;
Logger::Logger()
{
	debug_fds.insert(2);
}
void Logger::SetLevel(Logger::Level _level)
{
    level = _level;
}
void Logger::Print(const char* format, va_list args)
{
    for(set<int>::const_iterator i=debug_fds.begin(); i!=debug_fds.end(); i++)
    {
        int fd = *i;
        va_list pars;
        va_copy(pars, args);
        dprintf(fd, "[pid: %5d]", getpid());
        vdprintf(fd, format, pars);
        dprintf(fd, "\n");
        va_end(pars);
    }
}
void Logger::Debug(const char* format, va_list args)
{
    if(level <= DEBUG)
        Print(format, args);
}
void Logger::Warning(const char* format, va_list args)
{
    if(level <= WARNING)
        Print(format, args);
}
void Logger::Error(const char* format, va_list args)
{
    if(level <= ERROR)
        Print(format, args);
}
void Logger::Fail(int err, const char* format, va_list args)
{
    if(level <= CRITICAL)
    {
        for(set<int>::const_iterator i=debug_fds.begin(); i!=debug_fds.end(); i++)
        {
            int fd = *i;
            va_list pars;
            va_copy(pars, args);
            dprintf(fd, "[pid: %5d]", getpid());
            vdprintf(fd, format, pars);
            dprintf(fd, " (%s)\n", strerror(err));
            va_end(pars);
        }
    }
    exit(1);
}

Buffer::Buffer(size_t _size)
{
    size = _size;
    fill = 0;
    if (size)
    {
        buf = (char*)malloc(size);
        if (buf == NULL)
        {
            fprintf(stderr, "Runner buffer memory depleted %lu: %s\n", (unsigned long)size, strerror(errno));
            exit(1);
        }
    }
    else
        buf = NULL;
}
Buffer::~Buffer()
{
    if(buf)
        free(buf);
}
void Buffer::Append(void* data, size_t length)
{
    if (fill + length > size)
    {
        size_t nsize = max(fill+length, 2*size);
        char* nbuf = (char*)realloc(buf, nsize);
        if (nbuf == NULL)
        {
            fprintf(stderr, "Runner buffer memory depleted %lu: %s\n", (unsigned long)size, strerror(errno));
            exit(1);
        }
        size = nsize;
        buf = nbuf;
    }
    memcpy(buf+fill, data, length);
    fill += length;
}
string Buffer::String() const
{
    return string(buf, fill);
}
int Buffer::YamlWriteCallback(void* data, unsigned char* buffer, size_t size)
{
    Buffer* buf = (Buffer*)data;
    buf->Append(buffer, size);
    return 1;
}
size_t Buffer::CurlWriteCallback(void* buffer, size_t size, size_t nmemb, void* userp)
{
    Buffer* buf = (Buffer*)userp;
    buf->Append(buffer, size * nmemb);
    return nmemb;
}

ProcStats::ProcStats(int _pid)
{
    FILE* f;
    char filename[32];
    sprintf(filename, "/proc/%d/stat", _pid);
    f = fopen(filename, "r");
    if (!f)
        Fail("read of '/proc/%d/stat' failed", _pid);
    char* buf = NULL;
    char* sta = NULL;
    int z;
//  if ((z = fscanf(f, "%d(%a[^)])%c%d%d%d%d%d%u%lu%lu%lu%lu%lu%lu%ld%ld%ld%ld%ld%ld%llu%lu%ld%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%d%d%u%u%llu%lu%ld",
    if ((z = fscanf(f, "%d%as%as%d%d%d%d%d%u%lu%lu%lu%lu%lu%lu%ld%ld%ld%ld%ld%ld%llu%lu%ld%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%d%d%u%u%llu%lu%ld",
        &pid, &buf, &sta, &ppid, &pgrp, &sid, &tty, &tpgid, &flags, &minflt, &cminflt, &majflt, &cmajflt, &utime, &stime, &cutime, &cstime, &priority, &nice, &threads, &alarm, &start_time, &vsize, &rss, &rss_lim, &start_code, &end_code, &start_stack, &esp, &eip, &signal, &blocked, &sig_ignore, &sig_catch, &wchan, &nswap, &cnswap, &exit_signal, &cpu_number, &sched_priority, &sched_policy, &io_delay, &guest_time, &cguest_time
    )) != 44)
        Fail("scanf of '/proc/%d/stat' failed %d %d %s %c %d", _pid, z, pid, buf, state, ppid);
    if (buf)
    {
        if (strlen(buf) >= 2)
            command = string(buf+1, strlen(buf)-2);
        free(buf);
    }
    if (sta)
    {
        state = sta[0];
        free(sta);
    }
    fclose(f);
    sprintf(filename, "/proc/%d/statm", _pid);
    f = fopen(filename, "r");
    if (!f)
        Fail("read of '/proc/%d/statm' failed", _pid);
    if (fscanf(f, "%llu%llu%llu%llu%llu%llu%llu",
        &mem_size, &mem_resident, &mem_shared, &mem_text, &mem_lib, &mem_data, &mem_dirty
    ) != 7)
        Fail("scanf of '/proc/%d/statm' failed", _pid);
    unsigned psize = getpagesize();
    mem_size *= psize;
    mem_resident *= psize;
    mem_shared *= psize;
    mem_text *= psize;
    mem_lib *= psize;
    mem_data *= psize;
    mem_dirty *= psize;

    fclose(f);
}
void UserInfo::set(void* _p)
{
    passwd* p = (passwd*)_p;
    ok = true;
    name = p->pw_name;
    password = p->pw_passwd;
    uid = p->pw_uid;
    gid = p->pw_gid;
    gecos = p->pw_gecos;
    dir = p->pw_dir;
    shell = p->pw_shell;
}
UserInfo::UserInfo(const string& name)
{
    ok = false;
    if(name == "")
        return;
    passwd pwd;
    passwd* ppwd;
    char buf[8192];
    getpwnam_r(name.c_str(), &pwd, buf, sizeof(buf), &ppwd);
    if (ppwd == &pwd)
        set(ppwd);
    else
    {
        char* eptr;
        long id = strtol(name.c_str(), &eptr, 10);
        if(eptr && *eptr == 0)
            getpwuid_r(id, &pwd, buf, sizeof(buf), &ppwd);
            if (ppwd == &pwd)
                set(ppwd);
    }
}
UserInfo::UserInfo(int id)
{
    ok = false;
    passwd pwd;
    passwd* ppwd;
    char buf[8192];
    getpwuid_r(id, &pwd, buf, sizeof(buf), &ppwd);
    if (ppwd == &pwd)
        set(ppwd);
}
void GroupInfo::set(void* _g)
{
    struct group* g = (struct group*)_g;
    ok = true;
    name = g->gr_name;
    password = g->gr_passwd;
    gid = g->gr_gid;
    members.clear();
    for(char** i=g->gr_mem; *i != NULL; i++)
        members.push_back(*i);
}
GroupInfo::GroupInfo(const string& name)
{
    ok = false;
    if(name == "")
        return;
    struct group grp;
    struct group* pgrp;
    char buf[8192];
    getgrnam_r(name.c_str(), &grp, buf, sizeof(buf), &pgrp);
    if(pgrp == &grp)
        set(pgrp);
    else
    {
        char* eptr;
        long id = strtol(name.c_str(), &eptr, 10);
        if(eptr && *eptr == 0)
        getgrgid_r(id, &grp, buf, sizeof(buf), &pgrp);
        if(pgrp == &grp)
            set(pgrp);
    }
}
GroupInfo::GroupInfo(int id)
{
    ok = false;
    struct group grp;
    struct group* pgrp;
    char buf[8192];
    getgrgid_r(id, &grp, buf, sizeof(buf), &pgrp);
    if(pgrp == &grp)
        set(pgrp);
}

MountsInfo::MountsInfo()
{
    FILE* f;
    f = fopen("/proc/mounts", "r");
    if (!f)
        Fail("read of '/proc/mounts' failed");
    char* so = NULL;
    char* ta = NULL;
    char* ty = NULL;
    char* op = NULL;
    while (true)
    {
        int z;
        if ((z = fscanf(f, "%as%as%as%as%*d%*d", &so, &ta, &ty, &op)) != 4)
            break;
        mounts.push_back(Mount(so, ta, ty, op));
        targets[ta] = mounts.back();
        map<string, Mount>::iterator t = targets.find(ta);
        t++;
        if (t != targets.end())
        {
            map<string, Mount>::iterator u = t;
            while (strncmp(ta, u->first.c_str(), strlen(ta)) != 0)
                u++;
            if (t != u)
                targets.erase(t, u);
        }
        free(so);
        free(ta);
        free(ty);
        free(op);
    }
    fclose(f);
}
bool MountsInfo::Available()
{
    struct stat s;
    if (stat("/proc/mounts", &s))
        return false;
    return major(s.st_dev) == 0;
}

Runner::~Runner()
{
    Stop();
}

void Debug(const char* format, ...)
{
    va_list args;
    va_start(args, format);
    Logger::Debug(format, args);
    va_end(args);
}
void Warning(const char* format, ...)
{
    va_list args;
    va_start(args, format);
    Logger::Warning(format, args);
    va_end(args);
}
void Fail(const char* format, ...)
{
    int err = errno;
    va_list args;
    va_start(args, format);
    Logger::Fail(err, format, args);
    va_end(args);
}

void Runner::set_rlimit(const string& name, int resource, long limit)
{
    struct rlimit r;
    r.rlim_cur = limit;
    r.rlim_max = limit;
    if (setrlimit(resource, &r))
        Fail("setrlimit('%s') failed", name.c_str());
    if (getrlimit(resource, &r))
        Fail("getrlimit('%s') failed", name.c_str());
    if ((long)r.rlim_cur != limit || (long)r.rlim_max != limit)
        Fail("setrlimit('%s') did not work", name.c_str());
}
void Runner::drop_capabilities()
{
    for (unsigned long cap = 0; cap < CAP_LAST_CAP; cap++)
        if(prctl(PR_CAPBSET_DROP, cap))
            Fail("cap_bset_drop() failed");
    cap_t caps = cap_init();
    if (cap_set_proc(caps))
        Fail("cap_set_proc() failed");
}
void Runner::drop_capability(const string& name, int cap)
{
    if(prctl(PR_CAPBSET_DROP, (unsigned long) cap))
        Fail("cap_bset_drop('%s') failed", name.c_str());
    cap_value_t capt = (cap_value_t)cap;
    cap_t caps = cap_get_proc();
    if (caps == NULL)
        Fail("cap_get_proc('%s') failed", name.c_str());
    if(cap_set_flag(caps, CAP_EFFECTIVE, 1, &capt, CAP_CLEAR))
        Fail("cap_set_flag('%s') failed", name.c_str());
    if(cap_set_flag(caps, CAP_PERMITTED, 1, &capt, CAP_CLEAR))
        Fail("cap_set_flag('%s') failed", name.c_str());
    if(cap_set_flag(caps, CAP_INHERITABLE, 1, &capt, CAP_CLEAR))
        Fail("cap_set_flag('%s') failed", name.c_str());
    if (cap_set_proc(caps))
        Fail("cap_set_proc('%s') failed", name.c_str());
    if(cap_free(caps))
        Fail("cap_free('%s') failed", name.c_str());
}

long miliseconds(const timeval& tv)
{
    long msecs = tv.tv_sec;
    msecs *= 1000;
    msecs += tv.tv_usec / 1000;
    return msecs;
}
long miliseconds(const timespec& ts)
{
    long msecs = ts.tv_sec;
    msecs *= 1000;
    msecs += ts.tv_nsec / 1000000;
    return msecs;
}
void ms_timeval(long ms, timeval& tv)
{
    tv.tv_sec = ms/1000;
    tv.tv_usec = (ms%1000)*1000;
}
void ms_timespec(long ms, timespec& ts)
{
    ts.tv_sec = ms/1000;
    ts.tv_nsec = (ms%1000)*1000000;
}
CpuTimes miliseconds(const rusage& usage)
{
    return CpuTimes(miliseconds(usage.ru_utime), miliseconds(usage.ru_stime));
};
CpuTimes miliseconds(const ProcStats& stat)
{
    return CpuTimes(stat.utime*1000/sysconf(_SC_CLK_TCK), stat.stime*1000/sysconf(_SC_CLK_TCK));
};
CpuTimes miliseconds(const Controller::Stats& stat)
{
    const long CGROUP_CPU_CLK_TCK = HZ;
    return CpuTimes(stat.utime*1000/CGROUP_CPU_CLK_TCK, stat.stime*1000/CGROUP_CPU_CLK_TCK, stat.time/1000000);
};
bool Runner::milisleep(long ms)
{
    return usleep(ms*1000);
};

bool Controller::Parse(const string& yaml, map<string, string>& data)
{
    yaml_parser_t parser;
    yaml_event_t event;
    yaml_parser_initialize(&parser);
    yaml_parser_set_input_string(&parser, (const unsigned char*)yaml.c_str(), yaml.length());
    int mode = 0;
    string key,val;
    data.clear();
    while (true)
    {
        if (!yaml_parser_parse(&parser, &event))
        {
            Debug("YAML Parser failure: %s", parser.problem);
            yaml_parser_delete(&parser);
            return false;
        }
        if (mode == 0 && event.type == YAML_STREAM_START_EVENT)
            mode = 1;
        else if (mode == 1 && event.type == YAML_DOCUMENT_START_EVENT)
            mode = 2;
        else if (mode == 2 && event.type == YAML_MAPPING_START_EVENT)
            mode = 3;
        else if (mode == 3 && event.type == YAML_SCALAR_EVENT)
        {
            key = string((const char*)event.data.scalar.value, (size_t)event.data.scalar.length);
            mode = 4;
        }
        else if (mode == 4 && event.type == YAML_SCALAR_EVENT)
        {
            val = string((const char*)event.data.scalar.value, (size_t)event.data.scalar.length);
            data[key] = val;
            mode = 3;
        }
        else if (mode == 3 && event.type == YAML_MAPPING_END_EVENT)
            mode = 5;
        else if (mode == 5 && event.type == YAML_DOCUMENT_END_EVENT)
            mode = 6;
        else if (mode == 6 && event.type == YAML_STREAM_END_EVENT)
        {
            yaml_event_delete(&event);
            break;
        }
        else
        {
            Debug("YAML Parser: wrong data");
            yaml_event_delete(&event);
            yaml_parser_delete(&parser);
            return false;
        }
        yaml_event_delete(&event);
    }
    yaml_parser_delete(&parser);
    return true;
}
bool Controller::Dump(const map<string, string>& data, string& yaml)
{
    yaml_emitter_t emitter;
    yaml_event_t event;
    yaml_emitter_initialize(&emitter);
    Buffer ybuf;
    yaml_emitter_set_output(&emitter, Buffer::YamlWriteCallback, &ybuf);

    yaml_stream_start_event_initialize(&event, YAML_UTF8_ENCODING);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter stream start failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }
    yaml_document_start_event_initialize(&event, NULL, NULL, NULL, 1);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter doc start failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }
    yaml_mapping_start_event_initialize(&event, NULL, NULL, 1, YAML_ANY_MAPPING_STYLE);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter map start failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }

    for (map<string,string>::const_iterator i = data.begin(); i != data.end(); i++)
    {
        yaml_scalar_event_initialize(&event, NULL, NULL, (unsigned char*)i->first.c_str(), i->first.length(), 1, 1, YAML_ANY_SCALAR_STYLE);
        if (!yaml_emitter_emit(&emitter, &event))
        {
            Debug("Emitter key failure: %s", emitter.problem);
            yaml_emitter_delete(&emitter);
            return false;
        }
        yaml_scalar_event_initialize(&event, NULL, NULL, (unsigned char*)i->second.c_str(), i->second.length(), 1, 1, YAML_ANY_SCALAR_STYLE);
        if (!yaml_emitter_emit(&emitter, &event))
        {
            Debug("Emitter val failure: %s", emitter.problem);
            yaml_emitter_delete(&emitter);
            return false;
        }
    }

    yaml_mapping_end_event_initialize(&event);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter map end failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }
    yaml_document_end_event_initialize(&event, 1);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter doc end failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }
    yaml_stream_end_event_initialize(&event);
    if (!yaml_emitter_emit(&emitter, &event))
    {
        Debug("Emitter stream end failure: %s", emitter.problem);
        yaml_emitter_delete(&emitter);
        return false;
    }

    yaml_emitter_delete(&emitter);
    yaml = ybuf.String();
    return true;
}

bool Controller::Contact(const string& action, const map<string, string>& input, map<string, string>& output)
{
    bool result = true;
    string yaml;
    if (!Dump(input, yaml))
        return false;
    //Debug("Contact yaml\n%s", yaml.c_str());

    char buf[16];
    snprintf(buf, sizeof(buf), "%d", port);
    string url = string("http://") + host + ":" + buf + "/" + action;
    //Debug("Contact url %s", url.c_str());

    CURL *curl;
    CURLcode res;
    curl = curl_easy_init();
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, yaml.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)yaml.length());
    Buffer cbuf;
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, Buffer::CurlWriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &cbuf);
    res = curl_easy_perform(curl);
    if(CURLE_OK != res)
        result = false;
    else
    {
        //Debug("Contact result\n%s", cbuf.String().c_str());
        if (!Parse(cbuf.String(), output))
            result = false;
    }
    curl_easy_cleanup(curl);
    return result;
}

void Controller::CheckOK(const std::string& call, const map<string, string>& output)
{
    map<string, string>::const_iterator ok = output.find("res");
    if (ok == output.end() || ok->second != "OK")
    {
        string yaml;
        Dump(output, yaml);
        Fail("%s returned '%s'", call.c_str(), yaml.c_str());
    }
}

Controller::Controller(const string& _host, int _port)
{
    host = _host;
    port = _port;
}

void Controller::GroupCreate(const string& cgroup)
{
    map<string, string> input, output;
    input["group"] = cgroup;
    Contact("CREATECG", input, output);
    CheckOK("CREATECG", output);
}
void Controller::GroupJoin(const string& cgroup)
{
    map<string, string> input, output;
    input["group"] = cgroup;
    char buf[64];

    timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    snprintf(buf, sizeof(buf), "__cgroup__.%ld.%ld.%ld.lock", (long)ts.tv_sec, (long)ts.tv_nsec, (long) ((char*)this - NULL));
    input["file"] = buf;
    snprintf(buf, sizeof(buf), "/tmp/%s", input["file"].c_str());
    int fd = open(buf, O_WRONLY | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR);
    if (fd < 0)
        Fail("open('%s') failed", input["file"].c_str());
    Contact("ASSIGNCG", input, output);
    close(fd);
    if (unlink(buf))
        Fail("unlink('%s') failed", buf);
    CheckOK("ASSIGNCG", output);
}
void Controller::GroupDestroy(const string& cgroup)
{
    map<string, string> input, output;
    input["group"] = cgroup;
    Contact("DESTROYCG", input, output);
    CheckOK("DESTROYCG", output);
}
void Controller::GroupLimits(const string& cgroup, const Limits& limits)
{
    map<string, string> input, output;
    if (limits.memory > 0)
    {
        char buf[32];
        snprintf(buf, sizeof(buf), "%ld", limits.memory);
        input["memory"] = buf;
    }
    if (input.size() > 0)
    {
        input["group"] = cgroup;
        Contact("LIMITCG", input, output);
        CheckOK("LIMITCG", output);
    }
}
Controller::Stats Controller::GroupStats(const string& cgroup)
{
    map<string, string> input, output;
    input["group"] = cgroup;
    Contact("QUERYCG", input, output);
    CheckOK("QUERYCG", output);
    Stats s;
    s.memory = atol(output["memory"].c_str());
    s.time = atol(output["cpu"].c_str());
    s.utime = atol(output["cpu.user"].c_str());
    s.stime = atol(output["cpu.system"].c_str());
    return s;
}


bool Runner::check_times()
{
//  rusage usage;
    timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts))
        Fail("clock_gettime(CLOCK_REALTIME) failed");
    long realtimesofar = miliseconds(ts) - start_time;
    CpuTimes proctimesofar = dead_pids_time;
    unsigned long long curmemory = 0;
    for (set<int>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
    {
        /* NIE DA SIE TAK, A POWINNO! Musimy czytać wolnego proca w sighandlerze
        getrusage(*i, &usage);
        proctimesofar += miliseconds(usage.ru_utime);
        */
        ProcStats stat(*i);
        proctimesofar += miliseconds(stat);
        curmemory += stat.mem_size;
    }
    if (proctimesofar.user < 0 || proctimesofar.system < 0 || proctimesofar.time < 0)
    {
        Debug("CPU time below zero: (%ld + %ld = %ld)", proctimesofar.user, proctimesofar.system, proctimesofar.time);
        proctimesofar = CpuTimes(0,0);
    }
    if (realtimesofar < 0)
    {
        Debug("Real time below zero: %ld", realtimesofar);
        realtimesofar = 0;
    }
    result.real_time = realtimesofar;
    result.cpu_time = proctimesofar.time;
    result.user_time = proctimesofar.user;
    result.system_time = proctimesofar.system;
    result.memory = max((unsigned long long)result.memory, curmemory/1024);
    if ((cpu_time > 0 && cpu_time < (long)result.cpu_time) ||
            (real_time > 0 && real_time < (long)result.real_time) ||
            (user_time > 0 && user_time < (long)result.user_time) ||
            (system_time > 0 && system_time < (long)result.system_time))
    {
        result.SetStatus(Result::RES_TIME);
        return false;
    }
    if ((memory_space > 0) && ((long)curmemory > memory_space))
    {
        result.SetStatus(Result::RES_MEMORY);
        return false;
    }
    return true;
}
bool Runner::check_cgroup()
{
    if (cgroup != "" && controller)
    {
        Controller::Stats stats = controller->GroupStats(cgroup);
        result.cgroup_memory = stats.memory;
        CpuTimes cgtime = miliseconds(stats);
        result.cgroup_time = cgtime.time;
        result.cgroup_user_time = cgtime.user;
        result.cgroup_system_time = cgtime.system;
        if ((cgroup_time > 0 && cgroup_time < (long)result.cgroup_time) ||
                (cgroup_user_time > 0 && cgroup_user_time < (long)result.cgroup_user_time) ||
                (cgroup_system_time > 0 && cgroup_system_time < (long)result.cgroup_system_time))
        {
            result.SetStatus(Result::RES_TIME);
            return false;
        }
        if (cgroup_memory > 0 && cgroup_memory < (long)result.cgroup_memory)
        {
            result.SetStatus(Result::RES_MEMORY);
            return false;
        }
    }
    return true;
}

int total_write(int fd, const void* buf, size_t cnt) {
    while (cnt>0) {
        ssize_t w = write(fd, buf, cnt);
        if (w < 0)
            return w;
        buf = ((char*)buf)+w;
        cnt -= w;
    }
    return 0;
}
int total_read(int fd, void* buf, size_t cnt) {
    while (cnt>0) {
        ssize_t r = read(fd, buf, cnt);
        if (r < 0)
            return r;
        buf = ((char*)buf)+r;
        cnt -= r;
    }
    return 0;
}

int cat_open(const char* path, int oflag, int mode) {
    int catpipe[2];
    int ctrlpipe[2];
    if (pipe(catpipe))
        Fail("pipe failed");
    if (pipe(ctrlpipe))
        Fail("pipe failed");
    int f = fork();
    if (f<0)
        Fail("fork failed");
    if (f==0) {
        close(ctrlpipe[0]);
        close(catpipe[1]);

        f = fork();
        if (f < 0) {
            total_write(ctrlpipe[1], &f, sizeof(f));
            exit(1);
        }
        if (f > 0)
            exit(0);
        umask(0);
        f = setsid();
        if (f < 0) {
            total_write(ctrlpipe[1], &f, sizeof(f));
            exit(1);
        }
        f = chdir("/");
        if (f < 0) {
            total_write(ctrlpipe[1], &f, sizeof(f));
            exit(1);
        }
        for (int f=getdtablesize(); f >= 0; f--)
            if (f!=ctrlpipe[1] && f!=catpipe[0])
                close(f);

        int fd = open(path, oflag, mode);
        total_write(ctrlpipe[1], &fd, sizeof(fd));
        close(ctrlpipe[1]);
        if (fd < 0)
            exit(1);
        char buf[4096];
        while (true) {
            int r = read(catpipe[0], buf, 4096);
            if (r < 0)
                exit(0);
            total_write(fd, buf, r);
        }
    }
    close(ctrlpipe[1]);
    close(catpipe[0]);
    total_read(ctrlpipe[0], &f, sizeof(f));
    close(ctrlpipe[0]);
    if (f<0)
        Fail("cat_open failed");
    return catpipe[1];
}


void Runner::run_child()
{
    // Synchronize myself to run after my parent has registered me in runners
    char rbuf[1];
    close(pipefd[1]);
    while (read(pipefd[0], rbuf, 1) > 0)
        ;
    close(pipefd[0]);

    Initializer::Stop();

    if (ptrace)
        if (::ptrace(PTRACE_TRACEME, 0, NULL, NULL))
            Fail("ptrace_traceme failed");

/*
    if (setpgrp())
        Fail("setpgrp() failed");
*/

    if (setsid() < 0)
        Fail("setsid() failed");

    munlockall();
    if (lock_memory)
        mlockall(MCL_CURRENT | MCL_FUTURE);

    uid_t ruid, euid, suid;
    gid_t rgid, egid, sgid;
    getresuid(&ruid, &euid, &suid);
    getresgid(&rgid, &egid, &sgid);
    uid_t uid;
    gid_t gid;

    uid = ruid;
    gid = rgid;

    UserInfo usr(user);
    if (usr.ok)
    {
        uid = usr.uid;
        gid = usr.gid;
    }
    GroupInfo grp(group);
    if (grp.ok)
    {
        gid = grp.gid;
    }


    setresgid(rgid, rgid, egid);
    setresuid(ruid, ruid, euid);
    int fi=-1, fo=-1, fe=-1;
    if ((input != "") && ((fi = open(input.c_str(), O_RDONLY)) < 0))
        Fail("open('%s') failed", input.c_str());
    if ((output != "") && ((fo = cat_open(output.c_str(), O_WRONLY|O_CREAT|(output_trunc?O_TRUNC:O_APPEND), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH )) < 0))
        Fail("open('%s') failed", output.c_str());
    if (error_to_output)
        fe = fo;
    else if ((error != "") && ((fe = cat_open(error.c_str(), O_WRONLY|O_CREAT|(error_trunc?O_TRUNC:O_APPEND), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)) < 0))
        Fail("open('%s') failed", error.c_str());
    setresgid(rgid, egid, sgid);
    setresuid(ruid, euid, suid);

    string username("unknown");
    string homedir("/");
    string shell("/bin/bash");
    UserInfo ust(uid);
    if (ust.ok)
    {
        username = ust.name;
        homedir = ust.dir;
        shell = ust.shell;
    }

    if ((dir != "") && chdir(dir.c_str()))
        Fail("chdir('%s') failed", dir.c_str());
    if (dir != "")
    {
        if (new_mount && pivot)
        {
            const char* oldroot = "tmp/__oldroot__";
            bool rem = (mkdir(oldroot, S_IRUSR | S_IWUSR | S_IXUSR) == 0);
            if(mount(oldroot, oldroot, "", MS_BIND, NULL))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("bind mount('%s') failed", oldroot);
            }
            if(mount(oldroot, oldroot, "", MS_PRIVATE, NULL))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("private mount('%s') failed", oldroot);
            }
            if (syscall(SYS_pivot_root, ".", oldroot))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("pivot_root('.', '%s') failed", oldroot);
            }
            if (chdir("/"))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("chdir('/') failed");
            }
            if(umount2(oldroot, MNT_DETACH))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("first detach('%s') failed", oldroot);
            }
            if(umount2(oldroot, MNT_DETACH))
            {
                if (rem)
                    rmdir(oldroot);
                Fail("second detach('%s') failed", oldroot);
            }
            if (rem)
                rmdir(oldroot);
        }
        else if (chroot("."))
            Fail("chroot('.') failed");
    }
    if (work_dir != "")
    {
        if (chdir(work_dir.c_str()))
            Fail("chdir('%s') failed", work_dir.c_str());
    }
    else
        if (chdir("/"))
            Fail("chdir('/') failed");

    if (new_mount && mount_proc)
    {
        umount2("/proc", MNT_DETACH);
        if (mount("proc", "/proc", "proc", 0, NULL))
            Fail("mount('proc', '/proc', 'proc') failed");
    }

    if (cgroup != "" && controller)
    {
        Controller::Limits limits;
        //if (cgroup_memory > 0)
        //    limits.memory = cgroup_memory;
        controller->GroupLimits(cgroup, limits);
        controller->GroupJoin(cgroup);
    }

    if ((env_level != ENV_COPY) && clearenv())
        Fail("clearenv failed");
    switch(env_level)
    {
        case ENV_FULL:
            if (setenv("TERM", "linux", 1)) Fail("setenv('TERM') failed");
            if (setenv("CFLAGS", "-Wall -O2", 1)) Fail("setenv('CFLAGS') failed");
            if (setenv("CPPFLAGS", "-Wall -O2", 1)) Fail("setenv('CPPFLAGS') failed");
            if (setenv("USER", username.c_str(), 1)) Fail("setenv('USER') failed");
            if (setenv("USERNAME", username.c_str(), 1)) Fail("setenv('USERNAME') failed");
            if (setenv("LOGNAME", username.c_str(), 1)) Fail("setenv('LOGNAME') failed");
            if (setenv("SHELL", shell.c_str(), 1)) Fail("setenv('SHELL') failed");
            if (setenv("HOME", homedir.c_str(), 1)) Fail("setenv('HOME') failed");
            if (setenv("LANG", "en_US.UTF-8", 1)) Fail("setenv('LANG') failed");
            if (setenv("LANGUAGE", "en_US.UTF-8", 1)) Fail("setenv('LANGUAGE') failed");
        case ENV_SIMPLE:
            if (setenv("IFS", " ", 1)) Fail("setenv('IFS') failed");
            if (setenv("PWD", work_dir.c_str(), 1)) Fail("setenv('PWD') failed");
            if (setenv("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", 1)) Fail("setenv('PATH') failed");
        case ENV_COPY:
        case ENV_EMPTY:
            ;
    }
    for (map<string, string>::const_iterator i=env_add.begin(); i!=env_add.end(); i++)
        if (setenv(i->first.c_str(), i->second.c_str(), 1))
            Fail("setenv('%s') failed", i->first.c_str());
    for (set<string>::const_iterator i=env_del.begin(); i!=env_del.end(); i++)
        if (unsetenv(i->c_str()))
            Fail("unsetenv('%s') failed", i->c_str());

    set_rlimit("CORE", RLIMIT_CORE, 0);

    if (memory_space > 0)
    {
        set_rlimit("AS", RLIMIT_AS, memory_space);
        set_rlimit("DATA", RLIMIT_DATA, memory_space);
        set_rlimit("STACK", RLIMIT_STACK, memory_space);
    }
    if (stack_space > 0)
        set_rlimit("STACK", RLIMIT_STACK, min(stack_space, memory_space));
    if (data_space > 0)
        set_rlimit("DATA", RLIMIT_DATA, min(data_space, memory_space));


    if (priority > 0)
        if (setpriority(PRIO_PGRP, 0, 19-priority))
            Fail("setpriority(%d) failed", 19-priority);

    if (scheduler_cpu.size())
    {
        cpu_set_t *cpusetp;
        size_t cpusets = 1 + *max_element(scheduler_cpu.begin(), scheduler_cpu.end());
        if (!(cpusetp = CPU_ALLOC(cpusets)))
            Fail("cpu_alloc(%d) failed", (int)cpusets);
        cpusets = CPU_ALLOC_SIZE(cpusets);
        CPU_ZERO_S(cpusets, cpusetp);
        for (set<int>::const_iterator i = scheduler_cpu.begin(); i != scheduler_cpu.end(); i++)
            CPU_SET_S(*i, cpusets, cpusetp);
        if (sched_setaffinity(0, cpusets, cpusetp))
            Fail("setaffinity failed");
        CPU_FREE(cpusetp);
    }
    if (scheduler_policy >= 0)
    {
        sched_param schp;
        if (scheduler_priority > 0)
            schp.sched_priority = scheduler_priority;
        else
            schp.sched_priority = 0;
        if (sched_setscheduler(0, scheduler_policy, &schp))
            Fail("setscheduler failed");
    }

    if (uid < 0)
        uid = ruid;
    if (gid < 0)
        gid = rgid;
    setresgid(gid, gid, gid);
    setresuid(uid, uid, uid);

    if (cpu_time > 0)
        set_rlimit("CPU", RLIMIT_CPU, (cpu_time + 1999) / 1000);
    if (thread_count > 0)
        set_rlimit("THREAD", RLIMIT_NPROC, thread_count);

    if (fi >= 0)
    {
        if (dup2(fi, 0) < 0)
            Fail("dup2(stdin) failed");
    }
    else
        if(input != "") close(0);
    if (fo >= 0)
    {
        if (dup2(fo, 1) < 0)
            Fail("dup2(stdout) failed");
    }
    else
        if(output != "") close(1);
    if (fe >= 0)
    {
        if (dup2(fe, 2) < 0)
            Fail("dup2(stderr) failed");
    }
    else
        if(error != "") close(2);

    size_t buflen = exec.length() + 1;
    for (uint i=0; i < params.size(); i++)
        buflen += params[i].length() + 1;
    char* argv[params.size() + 2];
    char buf[buflen];
    strncpy(buf, exec.c_str(), exec.length() + 1);
    argv[0] = buf;
    buflen = exec.length() + 1;

    for (uint i=0; i < params.size(); i++)
    {
        strncpy(buf + buflen, params[i].c_str(), params[i].length() + 1);
        argv[1 + i] = buf + buflen;
        buflen += params[i].length() + 1;
    }
    argv[params.size() + 1] = NULL;

    if (cap_level == CAP_EMPTY)
        drop_capabilities();
    else
        switch (cap_level)
        {
            case CAP_SAFE:
                drop_capability("AUDIT_CONTROL", CAP_AUDIT_CONTROL);
                drop_capability("AUDIT_WRITE", CAP_AUDIT_WRITE);
                drop_capability("SYS_MODULE", CAP_SYS_MODULE);
                drop_capability("SYS_BOOT", CAP_SYS_BOOT);
                drop_capability("SYS_TIME", CAP_SYS_TIME);
                drop_capability("SYS_ADMIN", CAP_SYS_ADMIN);
            case CAP_COPY:
                drop_capability("SETPCAP", CAP_SETPCAP);
            case CAP_FULL:
            case CAP_EMPTY:
                ;
        }

    Debug("Environment initialized! Go!");
    for (int f=getdtablesize(); f >= 3; f--)
        close(f);
    if (descriptor_count > 0)
        set_rlimit("DESCRIPTORS", RLIMIT_NOFILE, descriptor_count);

    if(search_path)
        execvp(exec.c_str(), argv);
    else
        execv(exec.c_str(), argv);
    Fail("execv('%s') failed", exec.c_str());
}

void Runner::run_parent()
{
    Debug("spawn child %d", (int)child);
    Register(child, this);
    if (!ptrace)
        offspring.insert(child);

    timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts))
        Fail("clock_gettime(CLOCK_REALTIME) failed");
    start_time = miliseconds(ts);

    close(pipefd[1]);
    close(pipefd[0]);
}

void Runner::process_child(long epid)
{
    const long ptrace_opts = PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT;
    if (!check_times())
    {
        Stop();
        return;
    }
    int status;
    rusage usage;
    pid_t p = wait4(epid, &status, WNOHANG | WUNTRACED, &usage);
    if (p < 0 && errno != ECHILD)
        Fail("wait4 failed");
    if (p <= 0)
    {
        Debug("wait4 %d empty", (int)epid);
        return;
    }
    int sig = 0;
    if (WIFSTOPPED(status))
        sig = WSTOPSIG(status);
    else if (WIFSIGNALED(status))
        sig = WTERMSIG(status);
    if (offspring.find(p) == offspring.end())
    {
        if (ptrace)
        {
//      ::ptrace(PTRACE_ATTACH, p, NULL, NULL);
            ::ptrace(PTRACE_SETOPTIONS, p, NULL, ptrace_opts);
            if (sig == SIGTRAP)
                sig = SIGTRAP | 0x80;
        }
        offspring.insert(p);
        Register(p, this);
    }
    bool force_stop = false;

    if (WIFSTOPPED(status))
    {
        if (ptrace)
        {
            siginfo_t sigi;
            ::ptrace(PTRACE_GETSIGINFO, p, NULL, &sigi);

            if (sig == SIGTRAP)
            {
                int ptre = (status >> 16) & 0xffff;
                if (ptre == PTRACE_EVENT_FORK ||
                        ptre == PTRACE_EVENT_VFORK ||
                        ptre == PTRACE_EVENT_CLONE)
                {
                    //TODO: Handle new child? No need?
                    unsigned long npid;
                    ::ptrace(PTRACE_GETEVENTMSG, p, NULL, &npid);
                    Debug("-> Thread %d %lu", (int)p, npid);
                    /*
                    ::ptrace(PTRACE_ATTACH, npid, NULL, NULL);
                    ::ptrace(PTRACE_SETOPTIONS, npid, NULL, ptrace_opts);
                    offspring.insert(npid);
                    Register(npid, this);
                    */
                    ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
                    ::ptrace(PTRACE_SYSCALL, npid, NULL, NULL);
                    Debug("<- Thread %d %lu", (int)p, npid);
                }
                else if (ptre == PTRACE_EVENT_EXEC)
                {
                    //TODO: Allow him to exec?
                    Debug("-> Execing %d", (int)p);
                    ::ptrace(PTRACE_ATTACH, p, NULL, NULL);
                    ::ptrace(PTRACE_SETOPTIONS, p, NULL, ptrace_opts);
                    ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
                    Debug("<- Execing %d", (int)p);
                }
                else if (ptre == PTRACE_EVENT_EXIT)
                {
                    unsigned long exit_status;
                    ::ptrace(PTRACE_GETEVENTMSG, p, NULL, &exit_status);
                    Debug("-> Exiting %d %lu", (int)p, exit_status);
                    //TODO: Check something on exit?
                    ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
                    Debug("<- Exiting %d %lu", (int)p, exit_status);
                }
            }
            else if (sig == (SIGTRAP | 0x80))
            {
                user_regs_struct regs;
                ::ptrace(PTRACE_GETREGS, p, NULL, &regs);
#ifdef __x86_64__
#define orig_xax orig_rax
#define xbx rbx
#else
#define orig_xax orig_eax
#define xbx ebx
#endif
                switch (regs.orig_xax)
                {
                    case __NR_execve:
                        if(!after_exec)
                        {
                            Debug("First exec reached");
                            after_exec = true;
                        }
                        else if (ptrace_safe)
                        {
                            result.SetStatus(Result::RES_IO);
                            Stop();
                        }
                    case __NR_exit:
                        break;
                    case __NR_read:
                        break;
                    case __NR_write:
                        break;
                    case __NR_brk:
                        break;
                    case __NR_mmap:
                        break;
                    case __NR_munmap:
                        break;
                    case __NR_uname:
                        break;
                    case __NR_clone:
                        Debug("Clone");
                        unsigned long mod;
                        mod = CLONE_UNTRACED;
                        regs.xbx &= ~mod;
                        mod = CLONE_PTRACE;
                        regs.xbx |= mod;
                    default:
                        if (ptrace_safe)
                        {
                            result.SetStatus(Result::RES_IO);
                            Stop();
                        }
                    //TODO: Handle syscalls!
                }
                Debug("Syscall %d %d", (int)p, (int)regs.orig_xax);
                ::ptrace(PTRACE_SETREGS, p, NULL, &regs);
                ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
#undef xbx
#undef orig_xbx
            }
            else
            {
                Debug("-> Signaling %d %d", (int)p, (int)sigi.si_signo);
                ::ptrace(PTRACE_SYSCALL, p, NULL, sigi.si_signo);
            }
        }
        else
            force_stop = true;
    }
    else if (WIFEXITED(status) || WIFSIGNALED(status))
    {
        if(WIFEXITED(status))
            Debug("Exited %d", (int)p);
        if(WIFSIGNALED(status))
        {
            int s = WSTOPSIG(status);
            Debug("Signaled %d (%d)", (int)p, s);
        }
        dead_pids_time = miliseconds(usage);
        offspring.erase(p);
        Unregister(p);
        if (p == child)
        {
            result.exit_status = status;
            result.usage = usage;
            result.memory = max((long)result.memory, (long)usage.ru_maxrss);
            CpuTimes times = miliseconds(usage);
            result.cpu_time = max((long)result.cpu_time, (long)times.time);
            result.user_time = max((long)result.user_time, (long)times.user);
            result.system_time = max((long)result.system_time, (long)times.system);

            if (WIFEXITED(status) && (WEXITSTATUS(status) == 0))
                result.SetStatus(Result::RES_OK);
            else
                result.SetStatus(Result::RES_RUNTIME);
            Stop();
        }
    }
    else
        force_stop = true;
    if (p==child && force_stop)
    {
        Debug("Child stoped for unknown reason");
        result.SetStatus(Result::RES_RUNTIME);
        Stop();
    }
    else if (force_stop)
    {
        Debug("Grandchild stopped for unknown reason");
    }
}

int Runner::child_runner(void* _runner)
{
    Runner* runner = (Runner*) _runner;
    runner->run_child();
    return 0;
}

void Runner::Run()
{
    parent = getpid();
    if (debug_file != "")
    {
        int debfd;
        if ((debug_file != "") && ((debfd = open(debug_file.c_str(), O_WRONLY | O_CREAT | O_APPEND, S_IRUSR | S_IWUSR)) < 0))
            Fail("open('%s') failed", debug_file.c_str());
        else
            Logger::debug_fds.insert(debfd);
    }
    if (pivot && !new_mount)
        Fail("Can't run pivot without mount namespace");
    if (mount_proc && !new_mount)
        Fail("Can't run mount_proc without mount namespace");
    if (controller_host != "" || controller_port > 0)
        controller = new Controller(controller_host, controller_port);
    if (cgroup != "" && controller)
        controller->GroupCreate(cgroup);
    if (ptrace_safe)
        ptrace = true;
    if (user == "" && thread_count > 0)
        Warning("BEWARE! 'thread_count' sets limits for user, not for process group!");
    if (child > 0)
        Fail("run failed");
    if (pipe(pipefd))
        Fail("pipe failed");
    //if (cgroup_memory > 0 && memory_space <= 0)
    //{
    //    memory_space = cgroup_memory;
    //    Debug("Setting memory limit to cgroup memory limit");
    //}
    if (cgroup_time > 0 && cpu_time <= 0)
    {
        cpu_time = cgroup_time;
        Debug("Setting time limit to cgroup time limit");
    }
    if (cgroup_user_time > 0 && user_time <= 0)
    {
        user_time = cgroup_user_time;
        Debug("Setting user time limit to cgroup user time limit");
    }
    if (cgroup_system_time > 0 && system_time <= 0)
    {
        system_time = cgroup_system_time;
        Debug("Setting system time limit to cgroup system time limit");
    }
    after_exec = false;

    unsigned long flags = SIGCHLD;
    if (new_ipc)
        flags |= CLONE_NEWIPC;
    if (new_net)
        flags |= CLONE_NEWNET;
    if (new_mount)
        flags |= CLONE_NEWNS;
    if (new_pid)
        flags |= CLONE_NEWPID;
    if (new_uts)
        flags |= CLONE_NEWUTS;
    size_t cssize = 1024*1024;
    void *childstack, *stack = malloc(cssize);
    if (!stack)
        Fail("child stack malloc failed");

    childstack = (void*)((char*)stack + cssize);
    child = clone(child_runner, childstack, flags, (void*)this);
    if (child > 0)
        run_parent();
    else
        Fail("clone failed");
}

void Runner::Stop()
{
    if (child > 0)
    {
        if (ptrace)
        {
            ::ptrace(PTRACE_KILL, child, NULL, NULL);
            for (set<int>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
                ::ptrace(PTRACE_KILL, *i, NULL, NULL);
        }
        killpg(child, SIGKILL);
        check_times();
        check_cgroup();
        Unregister(child);
        for (set<int>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
            Unregister(*i);
        offspring.clear();
        child=-1;
        if (cgroup != "" && controller)
            controller->GroupDestroy(cgroup);
        result.SetStatus(Result::RES_STOP);
    }
}

bool Runner::Check()
{
    if (child <= 0)
        return false;
    if (!check_times() || !check_cgroup())
    {
        Stop();
        return false;
    }
    return true;
}

void Runner::Wait()
{
    while (child>0 && Check())
        Initializer::ProcessLoop(1000);
}

}
