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
#include <sstream>
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
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/user.h>
#include <sys/wait.h>

#include <linux/fs.h>
#include <linux/limits.h>
#include <linux/perf_event.h>

#include <asm/param.h>

#include <curl/curl.h>

#include "runner.h"

using namespace std;

namespace runner {

map<int, Runner*> Runner::runners;
bool Initializer::sigterm;
bool Initializer::sigalarm;
vector<int> Initializer::signals;
vector<struct sigaction> Initializer::handlers;
sem_t Logger::semaphore;
set<int> Logger::debug_fds;
Initializer Runner::initializer;
Logger Runner::logger;

Initializer::Initializer() {
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
void Initializer::Stop() {
    for (uint i=0; i<signals.size(); i++)
        sigaction(signals[i], &handlers[i], NULL);
}
void Initializer::SignalHandler(int sig, siginfo_t* info, void* data) {
    if (sig == SIGALRM)
        sigalarm = true;
    else if (sig == SIGTERM)
        sigterm = true;
}

void Runner::Register(int pid, Runner* runner) {
    if(runners.find(pid) == runners.end()) {
        runners[pid] = runner;
    }
    else
        Fail("Process %d was registered twice.\n", pid);
}
void Runner::Unregister(int pid) {
    runners.erase(pid);
}
void Runner::StopAll() {
    for (map<int, Runner*>::const_iterator i=runners.begin(); i!=runners.end(); i++)
        i->second->Stop();
}
void Runner::CheckAll() {
    for (map<int, Runner*>::const_iterator i=runners.begin(); i!=runners.end(); i++)
        i->second->Check();
}
void Runner::ProcessAChild(pid_t pid) {
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
    
void Initializer::Process() {
    if (sigterm) {
        sigterm = false;
        Runner::StopAll();
    }
    if (sigalarm) {
        sigalarm = false;
        Runner::CheckAll();
    }
    siginfo_t info;
    while (true) {
        info.si_pid = 0;
        if (waitid(P_ALL, 0, &info, WEXITED | WSTOPPED | WNOHANG | WNOWAIT) < 0 && errno != ECHILD)
            Fail("waitid failed");
        if (info.si_pid == 0)
            break;
        int pid = info.si_pid;
        Runner::ProcessAChild(pid);
   }
}

void Initializer::ProcessLoop(double s) {
    timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    double to = to_seconds(ts)+s;
    sigset_t orig_mask, blocked_mask;
    sigemptyset(&blocked_mask);
    for(vector<int>::iterator it = Initializer::signals.begin(); it != Initializer::signals.end(); ++it)
        sigaddset(&blocked_mask, *it);
    while (true) {
        sigprocmask(SIG_BLOCK, &blocked_mask, &orig_mask);
        Process();
        clock_gettime(CLOCK_REALTIME, &ts);
        double rem = to - to_seconds(ts);
        if (rem <= 0)
            break;
        from_seconds(rem, ts);
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
Logger::Logger() {
    sem_init(&semaphore, 0, 1);
    debug_fds.insert(2);
}
void Logger::SetLevel(Logger::Level _level) {
    level = _level;
}
void Logger::Print(const char* format, va_list args) {
    sem_wait(&semaphore);
    for(set<int>::const_iterator i=debug_fds.begin(); i!=debug_fds.end(); i++) {
        int fd = *i;
        va_list pars;
        va_copy(pars, args);
        dprintf(fd, "[pid: %5d]", getpid());
        vdprintf(fd, format, pars);
        dprintf(fd, "\n");
        va_end(pars);
    }
    sem_post(&semaphore);
}
void Logger::Debug(const char* format, va_list args) {
    if(level <= DEBUG)
        Print(format, args);
}
void Logger::Warning(const char* format, va_list args) {
    if(level <= WARNING)
        Print(format, args);
}
void Logger::Error(const char* format, va_list args) {
    if(level <= ERROR)
        Print(format, args);
}
void Logger::Fail(int err, const char* format, va_list args) {
    if(level <= CRITICAL) {
        for(set<int>::const_iterator i=debug_fds.begin(); i!=debug_fds.end(); i++) {
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

Buffer::Buffer(size_t _size) {
    size = _size;
    fill = 0;
    if (size) {
        buf = (char*)malloc(size);
        if (buf == NULL) {
            fprintf(stderr, "Runner buffer memory depleted %lu: %s\n", (unsigned long)size, strerror(errno));
            exit(1);
        }
    }
    else
        buf = NULL;
}
Buffer::~Buffer() {
    if(buf)
        free(buf);
}
void Buffer::Append(void* data, size_t length) {
    if (fill + length > size) {
        size_t nsize = max(fill+length, 2*size);
        char* nbuf = (char*)realloc(buf, nsize);
        if (nbuf == NULL) {
            fprintf(stderr, "Runner buffer memory depleted %lu: %s\n", (unsigned long)size, strerror(errno));
            exit(1);
        }
        size = nsize;
        buf = nbuf;
    }
    memcpy(buf+fill, data, length);
    fill += length;
}
string Buffer::String() const {
    return string(buf, fill);
}
size_t Buffer::CurlWriteCallback(void* buffer, size_t size, size_t nmemb, void* userp) {
    Buffer* buf = (Buffer*)userp;
    buf->Append(buffer, size * nmemb);
    return nmemb;
}

ProcStats::ProcStats(pid_t _pid) {
    FILE* f;
    char filename[32];
    sprintf(filename, "/proc/%d/stat", _pid);
    f = fopen(filename, "r");
    if (!f)
        Fail("read of '/proc/%d/stat' failed", _pid);
    char* buf = NULL;
    char* sta = NULL;
    int z;
    if ((z = fscanf(f, "%d%ms%ms%d%d%d%d%d%u%lu%lu%lu%lu%lu%lu%ld%ld%ld%ld%ld%ld%llu%lu%ld%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%d%d%u%u%llu%lu%ld",
        &pid, &buf, &sta, &ppid, &pgrp, &sid, &tty, &tpgid, &flags, &minflt, &cminflt, &majflt, &cmajflt, &utime, &stime, &cutime, &cstime, &priority, &nice, &threads, &alarm, &start_time, &vsize, &rss, &rss_lim, &start_code, &end_code, &start_stack, &esp, &eip, &signal, &blocked, &sig_ignore, &sig_catch, &wchan, &nswap, &cnswap, &exit_signal, &cpu_number, &sched_priority, &sched_policy, &io_delay, &guest_time, &cguest_time
    )) != 44)
        Fail("scanf of '/proc/%d/stat' failed %d %d %s %c %d", _pid, z, pid, buf, state, ppid);
    if (buf) {
        if (strlen(buf) >= 2)
            command = string(buf+1, strlen(buf)-2);
        free(buf);
    }
    if (sta) {
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
void UserInfo__set(UserInfo& ui, passwd* p) {
    ui.ok = true;
    ui.name = p->pw_name;
    ui.password = p->pw_passwd;
    ui.uid = p->pw_uid;
    ui.gid = p->pw_gid;
    ui.gecos = p->pw_gecos;
    ui.dir = p->pw_dir;
    ui.shell = p->pw_shell;
}
UserInfo::UserInfo(string name) {
    ok = false;
    if(name == "")
        return;
    passwd pwd;
    passwd* ppwd;
    char buf[8192];
    getpwnam_r(name.c_str(), &pwd, buf, sizeof(buf), &ppwd);
    if (ppwd == &pwd)
        UserInfo__set(*this, ppwd);
    else {
        char* eptr;
        long id = strtol(name.c_str(), &eptr, 10);
        if(eptr && *eptr == 0)
            getpwuid_r(id, &pwd, buf, sizeof(buf), &ppwd);
            if (ppwd == &pwd)
                UserInfo__set(*this, ppwd);
    }
}
UserInfo::UserInfo(uid_t id) {
    ok = false;
    passwd pwd;
    passwd* ppwd;
    char buf[8192];
    getpwuid_r(id, &pwd, buf, sizeof(buf), &ppwd);
    if (ppwd == &pwd)
        UserInfo__set(*this, ppwd);
}
UserInfo::UserInfo() : UserInfo(getuid()) {};
void GroupInfo__set(GroupInfo& gi, group* g) {
    gi.ok = true;
    gi.name = g->gr_name;
    gi.password = g->gr_passwd;
    gi.gid = g->gr_gid;
    gi.members.clear();
    for(char** i=g->gr_mem; *i != NULL; i++)
        gi.members.push_back(*i);
}
GroupInfo::GroupInfo(string name) {
    ok = false;
    if(name == "")
        return;
    struct group grp;
    struct group* pgrp;
    char buf[8192];
    getgrnam_r(name.c_str(), &grp, buf, sizeof(buf), &pgrp);
    if(pgrp == &grp)
        GroupInfo__set(*this, pgrp);
    else {
        char* eptr;
        long id = strtol(name.c_str(), &eptr, 10);
        if(eptr && *eptr == 0)
        getgrgid_r(id, &grp, buf, sizeof(buf), &pgrp);
        if(pgrp == &grp)
            GroupInfo__set(*this, pgrp);
    }
}
GroupInfo::GroupInfo(gid_t id) {
    ok = false;
    struct group grp;
    struct group* pgrp;
    char buf[8192];
    getgrgid_r(id, &grp, buf, sizeof(buf), &pgrp);
    if(pgrp == &grp)
        GroupInfo__set(*this, pgrp);
}
GroupInfo::GroupInfo() : GroupInfo(getgid()) {};

MountsInfo::MountsInfo() {
    FILE* f;
    f = fopen("/proc/mounts", "r");
    if (!f)
        Fail("read of '/proc/mounts' failed");
    char* so = NULL;
    char* ta = NULL;
    char* ty = NULL;
    char* op = NULL;
    while (true) {
        int z;
        if ((z = fscanf(f, "%ms%ms%ms%ms%*d%*d", &so, &ta, &ty, &op)) != 4)
            break;
        mounts.push_back(Mount(so, ta, ty, op));
        targets[ta] = mounts.back();
        map<string, Mount>::iterator t = targets.find(ta);
        t++;
        if (t != targets.end()) {
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
bool MountsInfo::Available() {
    struct stat s;
    if (stat("/proc/mounts", &s))
        return false;
    return major(s.st_dev) == 0;
}

Runner::~Runner() {
    Stop();
}

void Debug(const char* format, ...) {
    va_list args;
    va_start(args, format);
    Logger::Debug(format, args);
    va_end(args);
}
void Warning(const char* format, ...) {
    va_list args;
    va_start(args, format);
    Logger::Warning(format, args);
    va_end(args);
}
void Fail(const char* format, ...) {
    int err = errno;
    va_list args;
    va_start(args, format);
    Logger::Fail(err, format, args);
    va_end(args);
}

void Runner::set_rlimit(const string& name, int resource, long limit) {
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

double to_seconds(const timeval& tv) {
    double secs = tv.tv_sec;
    secs += (double) tv.tv_usec / (1000 * 1000);
    return secs;
}
double to_seconds(const timespec& ts) {
    long secs = ts.tv_sec;
    secs += (double) ts.tv_nsec / (1000 * 1000 * 1000);
    return secs;
}
void from_seconds(double s, timeval& tv) {
    tv.tv_sec = floor(s);
    tv.tv_usec = floor((s - floor(s)) * (1000 * 1000));
}
void from_seconds(double s, timespec& ts) {
    ts.tv_sec = floor(s);
    ts.tv_nsec = floor((s - floor(s)) * (1000 * 1000 * 1000));
}
CpuTimes::CpuTimes(const rusage& usage)
    : CpuTimes(to_seconds(usage.ru_utime), to_seconds(usage.ru_stime)) {};
CpuTimes::CpuTimes(const ProcStats& stat)
    : CpuTimes((double)stat.utime/sysconf(_SC_CLK_TCK), (double)stat.stime/sysconf(_SC_CLK_TCK)) {};
CpuTimes::CpuTimes(const Controller::Stats& stat)
    : CpuTimes((double)stat.utime/HZ, (double)stat.stime/HZ, (double)stat.time/1000 * 1000 * 1000) {};
bool Runner::sleep(double s) {
    return usleep(s * 1000 * 1000);
};

string urlescape(string data) {
    static CURL *curl = curl_easy_init();
    char *k = curl_easy_escape(curl, data.c_str(), data.length());
    string ret(k);
    curl_free(k);
    return ret;
}
string urlunescape(string data) {
    static CURL *curl = curl_easy_init();
    int kl;
    char *k = curl_easy_unescape(curl, data.c_str(), data.length(), &kl);
    string ret(k, kl);
    curl_free(k);
    return ret;
}

bool Controller::Parse(const string& code, map<string, string>& data)
{
    size_t la = 0;
    size_t le = 0;
    for(size_t i=0;true;i++)
        if(code[i] == '=')
            le = i;
        else if(i >= code.length() || code[i] == '&') {
            if(le > la and i > le) {
                string sk = urlunescape(code.substr(la, le-la));
                string sv = urlunescape(code.substr(le+1, i-le-1));
                data[sk] = sv;
            }
            if (i >= code.length())
                break;
            la = i+1;
        }
    return true;
}
bool Controller::Dump(const map<string, string>& data, string& code)
{
    code = "";
    for(const auto& kv : data) {
        if(code.length()>0)
            code += "&";
        code += urlescape(kv.first);
        code += "=";
        code += urlescape(kv.second);
    }
    return true;
}

bool Controller::Contact(const string& action, const map<string, string>& input, map<string, string>& output)
{
    bool result = true;
    string code;
    if (!Dump(input, code))
        return false;
    if (session != "") {
        if (code.length()>0)
            code += "&";
        code += "session_id=";
        code += urlescape(session);
        if (secret != "") {
            code += "&secret=";
            code += urlescape(secret);
        }
    }
    if (group != "") {
        if (code.length()>0)
            code += "&";
        code += "group=";
        code += urlescape(group);
    }

    char buf[16];
    snprintf(buf, sizeof(buf), "%d", port);
    string url = string("http://") + host + ":" + buf + "/" + action;

    CURL *curl;
    CURLcode res;
    curl = curl_easy_init();
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/x-www-form-urlencoded; charset=utf-8");
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, code.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)code.length());
    Buffer cbuf;
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, Buffer::CurlWriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &cbuf);
    res = curl_easy_perform(curl);
    if(CURLE_OK != res)
        result = false;
    else
    {
        if (!Parse(cbuf.String(), output))
            result = false;
    }
    curl_easy_cleanup(curl);
    return result;
}

void Controller::CheckOK(const std::string& call, const map<string, string>& output)
{
    map<string, string>::const_iterator ok = output.find("result");
    if (ok == output.end() || ok->second != "OK")
    {
        if (output.find("message") != output.end())
        {
            Fail("%s returned '%s'", call.c_str(), output.find("message")->second.c_str());
        } else {
            stringstream s;
            size_t c=output.size();
            s << "[";
            for(auto i = output.begin(); i != output.end(); i++, c--)
                s << i->first << ": " << i->second << (c>1?", ":"");
            s << "]";
            Fail("%s returned '%s'", call.c_str(), s.str().c_str());
        }
    }
}

Controller::Controller(string _host, int _port, string _session, string _secret, string _group) {
    host = _host;
    port = _port;
    session = _session;
    secret = _secret;
    group = _group;
    if (session == "" or secret == "") {
        map<string, string> input, output;
        Contact("", input, output);
        CheckOK("", output);
        session = output["session_id"];
        secret = output["secret"];
    }
}
void Controller::Attach() {
    map<string, string> input, output;
    char buf[64];

    snprintf(buf, sizeof(buf), "/tmp/runner_%s.lock", session.c_str());
    input["file"] = buf;
    int fd = open(buf, O_WRONLY | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR);
    if (fd < 0)
        Fail("open('%s') failed", input["file"].c_str());
    Contact("attach", input, output);
    CheckOK("attach", output);
    close(fd);
    if (unlink(buf))
        Fail("unlink('%s') failed", buf);
}
void Controller::Kill() {
    map<string, string> input, output;
    Contact("kill", input, output);
    CheckOK("kill", output);
}
void Controller::Close() {
    map<string, string> input, output;
    Contact("close", input, output);
    CheckOK("close", output);
}
void Controller::Limit(const Limits& limits) {
    map<string, string> input, output;
    if (limits.memory > 0) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%ld", limits.memory);
        input["memory"] = buf;
    }
    if (limits.cpus > 0) {
        char buf[32];
        snprintf(buf, sizeof(buf), "%ld", limits.cpus);
        input["cpus"] = buf;
    }
    if (input.size() > 0) {
        Contact("limit", input, output);
        CheckOK("limit", output);
    }
}
Controller::Stats Controller::Query() {
    map<string, string> input, output;
    Contact("query", input, output);
    CheckOK("query", output);
    Stats s;
    s.memory = atol(output["memory"].c_str());
    s.time = atol(output["cpu"].c_str());
    s.utime = atol(output["cpu.user"].c_str());
    s.stime = atol(output["cpu.system"].c_str());
    return s;
}

long perf_event_open(struct perf_event_attr *hw_event, pid_t pid, int cpu, int group_fd, unsigned long flags)
{
    int ret;
    ret = syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
    return ret;
}

PerfCounters::PerfCounters(pid_t pid)
    : fd_instructions(-1)
    , fd_cycles(-1)
{
    perf_event_attr attr;
    memset(&attr, 0, sizeof(struct perf_event_attr));
    attr.size    = sizeof(perf_event_attr);
    attr.type    = PERF_TYPE_HARDWARE;
    attr.config  = PERF_COUNT_HW_INSTRUCTIONS;
    attr.inherit = 1;
    attr.enable_on_exec = 1;

    //TODO: maybe, someday, we can do it using PERF_FLAG_PID_CGROUP ?
    fd_instructions = perf_event_open(&attr, pid, -1, -1, 0);
    //TODO: -1
    attr.config  = PERF_COUNT_HW_CPU_CYCLES;
    fd_cycles = perf_event_open(&attr, pid, -1, fd_instructions, 0);
    //TODO: -1
}
PerfCounters::~PerfCounters()
{
    if (fd_instructions >= 0)
        close(fd_instructions);
    if (fd_cycles >= 0)
        close(fd_cycles);
}
struct perf_read_format {
    unsigned long value;
//    unsigned long time_enabled;
//    unsigned long time_running;
//    unsigned long id;
};
PerfCounters::Stats PerfCounters::PerfStats()
{
    Stats s;
    perf_read_format res;
    if (fd_instructions >= 0) {
        ssize_t r = read(fd_instructions, &res, sizeof(res));
        if (r != sizeof(res)) {
            close(fd_instructions);
            s.instructions = 0;
            fd_instructions = -1;
        }
        s.instructions = res.value;
    } else
        s.instructions = 0;
    if (fd_cycles >= 0) {
        ssize_t r = read(fd_instructions, &res, sizeof(res));
        r = read(fd_cycles, &res, sizeof(res));
        if (r != sizeof(res)) {
            close(fd_cycles);
            s.cycles = 0;
            fd_cycles = -1;
        }
        s.cycles = res.value;
    } else
        s.cycles = 0;
    return s;
}

bool Runner::check_times()
{
//  rusage usage;
    timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts))
        Fail("clock_gettime(CLOCK_REALTIME) failed");
    long realtimesofar = to_seconds(ts) - start_time;
    CpuTimes proctimesofar = dead_pids_time;
    unsigned long long curmemory = 0;
    for (set<int>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
    {
        /* NIE DA SIE TAK, A POWINNO! Musimy czytać wolnego proca w sighandlerze
        getrusage(*i, &usage);
        proctimesofar += miliseconds(usage.ru_utime);
        */
        ProcStats stat(*i);
        proctimesofar += stat;
        curmemory += stat.mem_resident;
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
    PerfCounters::Stats perf_stats = perf->PerfStats();

    result.real_time = realtimesofar;
    result.cpu_time = proctimesofar.time;
    result.user_time = proctimesofar.user;
    result.system_time = proctimesofar.system;
    result.memory = max((unsigned long long)result.memory, curmemory/1024);
    result.perf_instructions = perf_stats.instructions;
    result.perf_cycles = perf_stats.cycles;
    if ((cpu_time > 0 && cpu_time < (long)result.cpu_time) ||
            (real_time > 0 && real_time < (long)result.real_time) ||
            (user_time > 0 && user_time < (long)result.user_time) ||
            (system_time > 0 && system_time < (long)result.system_time) ||
            (instructions > 0 && instructions < (long)result.perf_instructions) ||
            (cycles > 0 && cycles < (long)result.perf_cycles)
       )
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
    if (controller)
    {
        Controller::Stats stats = controller->Query();
        result.cgroup_memory = stats.memory;
        CpuTimes cgtime = stats;
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

int cat_open_read(const char* path, int oflag) {
    int catpipe[2];
    int ctrlpipe[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, catpipe))
        Fail("pipe failed");
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, ctrlpipe))
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
        for (int g=getdtablesize(); g >= 0; g--)
            if (g!=ctrlpipe[1] && g!=catpipe[0])
                close(g);

        int fd = open(path, oflag);

        f = chdir("/");
        if (f < 0) {
            total_write(ctrlpipe[1], &f, sizeof(f));
            exit(1);
        }

        total_write(ctrlpipe[1], &fd, sizeof(fd));
        close(ctrlpipe[1]);
        if (fd < 0)
            exit(1);
        char buf[4096];
        while (true) {
            int r = read(fd, buf, sizeof(buf));
            if (r <= 0) {
                close(fd);
                close(catpipe[0]);
                exit(0);
            }
            total_write(catpipe[0], buf, r);
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


int cat_open_write(const char* path, int oflag, int mode) {
    int catpipe[2];
    int ctrlpipe[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, catpipe))
        Fail("pipe failed");
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, ctrlpipe))
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
        for (int g=getdtablesize(); g >= 0; g--)
            if (g!=ctrlpipe[1] && g!=catpipe[0])
                close(g);

        int fd = open(path, oflag, mode);

        f = chdir("/");
        if (f < 0) {
            total_write(ctrlpipe[1], &f, sizeof(f));
            exit(1);
        }

        total_write(ctrlpipe[1], &fd, sizeof(fd));
        close(ctrlpipe[1]);
        if (fd < 0)
            exit(1);
        char buf[4096];
        while (true) {
            int r = read(catpipe[0], buf, sizeof(buf));
            if (r <= 0) {
                close(catpipe[0]);
                close(fd);
                exit(0);
            }
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


    if (setresgid(rgid, rgid, egid))
        Fail("setresgid failed");
    if (setresuid(ruid, ruid, euid))
        Fail("setresuid failed");
    int fi=-1, fo=-1, fe=-1;
    if ((input != "") && ((fi = cat_open_read(input.c_str(), O_RDONLY)) < 0))
        Fail("open('%s') failed", input.c_str());
    if ((output != "") && ((fo = cat_open_write(output.c_str(), O_WRONLY|O_CREAT|(output_trunc?O_TRUNC:O_APPEND), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH )) < 0))
        Fail("open('%s') failed", output.c_str());
    if (error_to_output)
        fe = fo;
    else if ((error != "") && ((fe = cat_open_write(error.c_str(), O_WRONLY|O_CREAT|(error_trunc?O_TRUNC:O_APPEND), S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH)) < 0))
        Fail("open('%s') failed", error.c_str());
    if (setresgid(rgid, egid, sgid))
        Fail("setresgid failed");
    if (setresuid(ruid, euid, suid))
        Fail("setresuid failed");

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
        if (dir != "" && chdir("/"))
            Fail("chdir('/') failed");

    if (new_mount && mount_proc)
    {
        umount2("/proc", MNT_DETACH);
        if (mount("proc", "/proc", "proc", 0, NULL))
            Fail("mount('proc', '/proc', 'proc') failed");
    }

    if (controller)
    {
        Controller::Limits limits;
        //if (cgroup_memory > 0)
        //    limits.memory = cgroup_memory;
        controller->Attach();
        controller->Limit(limits);
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

    if (uid < 0)
        uid = ruid;
    if (gid < 0)
        gid = rgid;
    if (setresgid(gid, gid, gid))
        Fail("setresgid failed");
    if (setresuid(uid, uid, uid))
        Fail("setresuid failed");

    if (cpu_time > 0)
        set_rlimit("CPU", RLIMIT_CPU, (cpu_time + 1999) / 1000);

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
    offspring.insert(child);

    timespec ts;
    if (clock_gettime(CLOCK_REALTIME, &ts))
        Fail("clock_gettime(CLOCK_REALTIME) failed");
    start_time = to_seconds(ts);

    perf = unique_ptr<PerfCounters>(new PerfCounters(child));

    close(pipefd[1]);
    close(pipefd[0]);
}

void Runner::process_child(long epid)
{
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
    if (offspring.find(p) == offspring.end())
    {
        offspring.insert(p);
        Register(p, this);
    }
    bool force_stop = false;

    if (WIFSTOPPED(status))
    {
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
        dead_pids_time = usage;
        offspring.erase(p);
        Unregister(p);
        if (p == child)
        {
            result.exit_status = status;
            result.memory = max((long)result.memory, (long)usage.ru_maxrss);
            CpuTimes times = usage;
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
    if (control_host != "" || control_port > 0)
        controller = new Controller(control_host, control_port, control_session, control_secret, cgroup);
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

void Runner::Stop() {
    if (child > 0) {
        killpg(child, SIGKILL);
        check_times();
        check_cgroup();
        Unregister(child);
        for (set<int>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
            Unregister(*i);
        offspring.clear();
        child=-1;
        if (controller)
            controller->Kill();
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
        Initializer::ProcessLoop(0.1);
}

}
