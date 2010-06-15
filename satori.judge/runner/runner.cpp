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

#include <curl/curl.h>
#include <yaml.h>

#include "runner.h"

using namespace std;

map<long, Runner*> Runner::runners;
vector<int> Runner::Initializer::signals;
vector<struct sigaction> Runner::Initializer::handlers;
Runner::Initializer Runner::initializer;
Runner::Initializer::Initializer()
{
  signals.push_back(SIGCHLD);
  handlers.resize(signals.size());
  struct sigaction action;
  memset(&action, 0, sizeof(action));
  action.sa_sigaction = &signalhandler;
  action.sa_flags = SA_RESTART | SA_SIGINFO;
  sigfillset(&action.sa_mask);
  for (uint i=0; i<signals.size(); i++)
    sigaction(signals[i], &action, &handlers[i]);
}
void Runner::Initializer::Stop()
{
  for (uint i=0; i<signals.size(); i++)
    sigaction(signals[i], &handlers[i], NULL);
}
void Runner::Initializer::signalhandler(int sig, siginfo_t* info, void* data)
{
  if (sig == SIGCHLD)
  {
    map<long, Runner*>::const_iterator i = runners.find(info->si_pid);
    if (i != runners.end())
      i->second->process_child();
    else
    {
      ProcStat P(info->si_pid, NULL);
      i = runners.find(P.ppid);
      if (i != runners.end())
        i->second->process_child();
      else
      {
        i = runners.find(P.pgrp);
        if (i != runners.end())
          i->second->process_child();
        else
          fprintf(stderr, "HANDLE: Received SIGCHLD from unknown pid %d\n", (int) info->si_pid);
      }
    }
  }
}

Runner::ProcStat::ProcStat(int _pid, Runner* runner)
{
  FILE* f;
  char filename[128];
  sprintf(filename, "/proc/%d/stat", _pid);
  f = fopen(filename, "r");
  if (!f)
    if (runner) runner->fail("read of '/proc/%d/stat' failed", _pid);
  char* buf = NULL;
  char* sta = NULL;
  int z;
//  if ((z = fscanf(f, "%d(%a[^)])%c%d%d%d%d%d%u%lu%lu%lu%lu%lu%lu%ld%ld%ld%ld%ld%ld%llu%lu%ld%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%d%d%u%u%llu%lu%ld",
  if ((z = fscanf(f, "%d%as%as%d%d%d%d%d%u%lu%lu%lu%lu%lu%lu%ld%ld%ld%ld%ld%ld%llu%lu%ld%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%lu%d%d%u%u%llu%lu%ld",
    &pid, &buf, &sta, &ppid, &pgrp, &sid, &tty, &tpgid, &flags, &minflt, &cminflt, &majflt, &cmajflt, &utime, &stime, &cutime, &cstime, &priority, &nice, &threads, &alarm, &start_time, &vsize, &rss, &rss_lim, &start_code, &end_code, &start_stack, &esp, &eip, &signal, &blocked, &sig_ignore, &sig_catch, &wchan, &nswap, &cnswap, &exit_signal, &cpu_number, &sched_priority, &sched_policy, &io_delay, &guest_time, &cguest_time
  )) != 44)
    if (runner) runner->fail("scanf of '/proc/%d/stat' failed %d %d %s %c %d", _pid, z, pid, buf, state, ppid);
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
    if (runner) runner->fail("read of '/proc/%d/statm' failed", _pid);
  if (fscanf(f, "%d%d%d%d%d%d%d",
    &mem_size, &mem_resident, &mem_shared, &mem_text, &mem_lib, &mem_data, &mem_dirty
  ) != 7)
    if (runner) runner->fail("scanf of '/proc/%d/statm' failed", _pid);
  fclose(f);
}
void Runner::UserStat::set(void* _p)
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
Runner::UserStat::UserStat(const string& name)
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
Runner::UserStat::UserStat(long id)
{
  ok = false;
  passwd pwd;
  passwd* ppwd;
  char buf[8192];
  getpwuid_r(id, &pwd, buf, sizeof(buf), &ppwd);
  if (ppwd == &pwd)
    set(ppwd);
}
void Runner::GroupStat::set(void* _g)
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
Runner::GroupStat::GroupStat(const string& name)
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
Runner::GroupStat::GroupStat(long id)
{
  ok = false;
  struct group grp;
  struct group* pgrp;
  char buf[8192];
  getgrgid_r(id, &grp, buf, sizeof(buf), &pgrp);
  if(pgrp == &grp)
    set(pgrp);
}

Runner::~Runner()
{
  Stop();
}

void Runner::debug(const char* format, ...)
{
  const char* who="PRE   : ";
  if (child==0)
    who="CHILD : ";
  else if (child>0)
    who="PARENT: ";

  fprintf(stderr, "%s", who);
  va_list args;
  va_start(args, format);
  vfprintf(stderr, format, args);
  va_end(args);
  fprintf(stderr, "\n");

  if (debfd >= 0)
  {
    dprintf(debfd, "%s", who);
    va_list args;
    va_start(args, format);
    vdprintf(debfd, format, args);
    va_end(args);
    dprintf(debfd, "\n");
  }
}

void Runner::fail(const char* format, ...)
{
  int err = errno;
  const char* who="PRE   : ";
  if (child==0)
    who="CHILD : ";
  else if (child>0)
    who="PARENT: ";
  fprintf(stderr, "%s", who);
  va_list args;
  va_start(args, format);
  vfprintf(stderr, format, args);
  va_end(args);
  fprintf(stderr, " (%s)\n", strerror(err));

  if (debfd >= 0)
  {
    dprintf(debfd, "%s", who);
    va_list args;
    va_start(args, format);
    vdprintf(debfd, format, args);
    va_end(args);
    dprintf(debfd, " (%s)\n", strerror(err));
  }

  result.status = RES_FAIL;
  exit(1);
}
void Runner::set_rlimit(const string& name, int resource, long limit)
{
  struct rlimit r;
  r.rlim_cur = limit;
  r.rlim_max = limit;
  if (setrlimit(resource, &r))
    fail("setrlimit('%s') failed", name.c_str());
  if (getrlimit(resource, &r))
    fail("getrlimit('%s') failed", name.c_str());
  if ((long)r.rlim_cur != limit || (long)r.rlim_max != limit)
    fail("setrlimit('%s') did not work", name.c_str());
}
void Runner::drop_capabilities()
{
  for (unsigned long cap = 0; cap < CAP_LAST_CAP; cap++)
    if(prctl(PR_CAPBSET_DROP, cap))
      fail("cap_bset_drop() failed");
  cap_t caps = cap_init();
  if (cap_set_proc(caps))
    fail("cap_set_proc() failed");
}
void Runner::drop_capability(const string& name, int cap)
{
  if(prctl(PR_CAPBSET_DROP, (unsigned long) cap))
    fail("cap_bset_drop('%s') failed", name.c_str());
  cap_value_t capt = (cap_value_t)cap;
  cap_t caps = cap_get_proc();
  if (caps == NULL)
    fail("cap_get_proc('%s') failed", name.c_str());
  if(cap_set_flag(caps, CAP_EFFECTIVE, 1, &capt, CAP_CLEAR))
    fail("cap_set_flag('%s') failed", name.c_str());
  if(cap_set_flag(caps, CAP_PERMITTED, 1, &capt, CAP_CLEAR))
    fail("cap_set_flag('%s') failed", name.c_str());
  if(cap_set_flag(caps, CAP_INHERITABLE, 1, &capt, CAP_CLEAR))
    fail("cap_set_flag('%s') failed", name.c_str());
  if (cap_set_proc(caps))
    fail("cap_set_proc('%s') failed", name.c_str());
  if(cap_free(caps))
    fail("cap_free('%s') failed", name.c_str());
}

long Runner::miliseconds(const timeval& tv)
{
  long usecs = tv.tv_sec;
  usecs *= 1000000;
  usecs += tv.tv_usec;
  return (usecs / 1000);
}
long Runner::miliseconds(const timespec& ts)
{
  long nsecs = ts.tv_sec;
  nsecs *= 1000000000;
  nsecs += ts.tv_nsec;
  return (nsecs / 1000000);
}
pair<long, long> Runner::miliseconds(const rusage& usage)
{
  return make_pair(miliseconds(usage.ru_utime), miliseconds(usage.ru_stime));
};
pair<long, long> Runner::miliseconds(const ProcStat& stat)
{
  return make_pair(stat.utime*1000/sysconf(_SC_CLK_TCK), stat.stime*1000/sysconf(_SC_CLK_TCK));
};
bool Runner::milisleep(long ms)
{
  return usleep(1000*ms);
};

bool Runner::parse_yaml(const string& yaml, map<string, string>& data)
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
      yaml_event_delete(&event);
      yaml_parser_delete(&parser);
      return false;
    }
    yaml_event_delete(&event);
  }
  yaml_parser_delete(&parser);
  return true;
}
bool Runner::dump_yaml(const map<string, string>& data, string& yaml)
{
  yaml_emitter_t emitter;
  yaml_event_t event;
  yaml_emitter_initialize(&emitter);
  size_t len = 1024;
  for(map<string,string>::const_iterator i = data.begin(); i != data.end(); i++)
    len += 8 + 4*i->first.length() + 4*i->second.length();
  unsigned char buf[len];
  size_t rlen = 0;

  fprintf(stderr, "Hello 1\n");

  yaml_emitter_set_output_string(&emitter, buf, len, &rlen);

  yaml_stream_start_event_initialize(&event, YAML_UTF8_ENCODING);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }
  fprintf(stderr, "Hello 2\n");
  yaml_document_start_event_initialize(&event, NULL, NULL, NULL, 0);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }
  yaml_mapping_start_event_initialize(&event, NULL, NULL, 0, YAML_ANY_MAPPING_STYLE);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }
  fprintf(stderr, "Hello 3\n");

  for (map<string,string>::const_iterator i = data.begin(); i != data.end(); i++)
  {
    fprintf(stderr, "Hello 3.5: %s\n", i->first.c_str());
    yaml_scalar_event_initialize(&event, NULL, NULL, (unsigned char*)i->first.c_str(), i->first.length(), 0, 0, YAML_ANY_SCALAR_STYLE);
    if (!yaml_emitter_emit(&emitter, &event))
    {
      yaml_emitter_delete(&emitter);
      return false;
    }
    fprintf(stderr, "Hello 3.5: %s\n", i->second.c_str());
    yaml_scalar_event_initialize(&event, NULL, NULL, (unsigned char*)i->second.c_str(), i->second.length(), 0, 0, YAML_ANY_SCALAR_STYLE);
    if (!yaml_emitter_emit(&emitter, &event))
    {
      yaml_emitter_delete(&emitter);
      return false;
    }
  }
  fprintf(stderr, "Hello 4\n");
  yaml_mapping_end_event_initialize(&event);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }
  fprintf(stderr, "Hello 4.5\n");
  yaml_document_end_event_initialize(&event, 0);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }
  fprintf(stderr, "Hello 5\n");
  yaml_stream_end_event_initialize(&event);
  if (!yaml_emitter_emit(&emitter, &event))
  {
    yaml_emitter_delete(&emitter);
    return false;
  }


  fprintf(stderr, "Hello 6\n");
  yaml_emitter_delete(&emitter);
  yaml = string((const char*)buf, rlen);
  return true;
}

bool Runner::contact_controller(string action, const map<string, string>& input, map<string, string>& output)
{
  bool result = true;
  string yaml;
  if (!dump_yaml(input, yaml))
    return false;
  debug("Contact YAML '%s'", yaml.c_str());

  char buf[16];
  snprintf(buf, sizeof(buf), "%d", controller_port);
  string url = string("http://") + controller_host + ":" + buf + "/" + action;
  debug("Contact URL '%s'", url.c_str());

  CURL *curl;
  CURLcode res;
  curl = curl_easy_init();
  curl_easy_setopt(curl, CURLOPT_URL, url.c_str());

  res = curl_easy_perform(curl);
  if(CURLE_OK != res)
    result = false;
  else
  {
//    yaml =
    if (!parse_yaml(yaml, output))
      result = false;
  }
  curl_easy_cleanup(curl);
  return result;
}

bool Runner::check_times()
{
//  rusage usage;
  timespec ts;
  if (clock_gettime(CLOCK_REALTIME, &ts)) fail("clock_gettime(CLOCK_REALTIME) failed");
  long realtimesofar = miliseconds(ts) - start_time;
  pair<long, long> proctimesofar = dead_pids_time;
  proctimesofar.first -= before_exec_time.first;
  proctimesofar.second -= before_exec_time.second;
  long curmemory = 0;
  for (set<long>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
  {
    /* NIE DA SIE TAK, A POWINNO! Musimy czytać wolnego proca w sighandlerze
    getrusage(*i, &usage);
    proctimesofar += miliseconds(usage.ru_utime);
    */
    ProcStat stat(*i, this);
    proctimesofar.first += miliseconds(stat).first;
    proctimesofar.second += miliseconds(stat).second;
    curmemory += stat.mem_size;
  }
  if (proctimesofar.first < 0 || proctimesofar.second < 0)
  {
    ProcStat stat(*offspring.begin(), this);
    debug("CPU time below zero: (%ld,%ld) = (%ld,%ld) - (%ld,%ld) + (%ld,%ld)", proctimesofar.first, proctimesofar.second, dead_pids_time.first, dead_pids_time.second, before_exec_time.first, before_exec_time.second, miliseconds(stat).first, miliseconds(stat).second);
    if (proctimesofar.first < 0)
      proctimesofar.first = 0;
    if (proctimesofar.second < 0)
      proctimesofar.second = 0;
  }
  if (realtimesofar < 0)
  {
    debug("Real time below zero: %ld", realtimesofar);
    realtimesofar = 0;
  }
  result.real_time = realtimesofar;
  result.cpu_time = proctimesofar.first + proctimesofar.second;
  result.user_time = proctimesofar.first;
  result.system_time = proctimesofar.second;
  result.memory = max((long)result.memory, curmemory);
  if (((cpu_time > 0) && (cpu_time < (long)result.cpu_time)) || ((real_time > 0) && (real_time < (long)result.real_time)) ||
      ((user_time > 0) && (user_time < (long)result.user_time)) || ((system_time > 0) && (system_time < (long)result.system_time)))
  {
    result.status = RES_TIME;
    Stop();
    return false;
  }
  if ((memory_space > 0) && (curmemory > memory_space))
  {
    result.status = RES_MEMORY;
    Stop();
    return false;
  }
  return true;
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

  result.status = RES_OK;
  
  if (ptrace)
    if (::ptrace(PTRACE_TRACEME, 0, NULL, NULL))
      fail("ptrace_traceme failed");

/*
  if (setpgrp())
    fail("setpgrp() failed");
*/

  if (setsid() < 0)
    fail("setsid() failed");

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

  UserStat usr(user);
  if (usr.ok)
  {
    uid = usr.uid;
    gid = usr.gid;
  }
  GroupStat grp(group);
  if (grp.ok)
  {
    gid = grp.gid;
  }


  setresgid(rgid, rgid, egid);
  setresuid(ruid, ruid, euid);
  int fi=-1, fo=-1, fe=-1;
  if ((input != "") && ((fi = open(input.c_str(), O_RDONLY)) < 0))
    fail("open('%s') failed", input.c_str());
  if ((output != "") && ((fo = open(output.c_str(), O_WRONLY|O_CREAT|(output_trunc?O_TRUNC:O_APPEND), 0644)) < 0))
    fail("open('%s') failed", output.c_str());
  if (error_to_output)
    fe = fo;
  else if ((error != "") && ((fe = open(error.c_str(), O_WRONLY|O_CREAT|(error_trunc?O_TRUNC:O_APPEND), 0644)) < 0))
    fail("open('%s') failed", error.c_str());
  setresgid(rgid, egid, sgid);
  setresuid(ruid, euid, suid);

  string username("unknown");
  string homedir("/");
  string shell("/bin/bash");
  UserStat ust(uid);
  if (ust.ok)
  {
    username = ust.name;
    homedir = ust.dir;
    shell = ust.shell;
  }

  if ((dir != "") && chdir(dir.c_str()))
    fail("chdir('%s') failed", dir.c_str());
  if (dir != "")
  {
    if (pivot)
    {
      bool rem = (mkdir("__oldroot__", S_IRUSR | S_IWUSR | S_IXUSR) == 0);
      if(mount("__oldroot__", "__oldroot__", "", MS_BIND, NULL))
        fail("bind mount('__oldroot__') failed");
      if(mount("__oldroot__", "__oldroot__", "", MS_PRIVATE, NULL))
        fail("private mount('__oldroot__') failed");
      if (syscall(SYS_pivot_root, ".", "__oldroot__"))
        fail("pivot_root('.', '__oldroot__') failed");
      if (chdir("/"))
        fail("chdir('/') failed");
      if(umount2("__oldroot__", MNT_DETACH))
        fail("first detach('__oldroot__') failed");
      if(umount2("__oldroot__", MNT_DETACH))
        fail("second detach('__oldroot__') failed");
      if (rem)
        rmdir("__oldroot__");
    }
    else if (chroot("."))
      fail("chroot('.') failed");
  }
  if (work_dir != "")
  {
    if (chdir(work_dir.c_str()))
      fail("chdir('%s') failed", work_dir.c_str());
  }
  else
    if (chdir("/"))
      fail("chdir('/') failed");

  if (new_pid && new_mount)
  {
    umount2("/proc", MNT_DETACH);
    mount("proc", "/proc", "proc", 0, NULL);
  }


  if ((env_level != ENV_COPY) && clearenv())
    fail("clearenv failed");
  switch(env_level)
  {
    case ENV_FULL:
      if (setenv("TERM", "linux", 1)) fail("setenv('TERM') failed");
      if (setenv("CFLAGS", "-Wall -O2", 1)) fail("setenv('CFLAGS') failed");
      if (setenv("CPPFLAGS", "-Wall -O2", 1)) fail("setenv('CPPFLAGS') failed");
      if (setenv("USER", username.c_str(), 1)) fail("setenv('USER') failed");
      if (setenv("USERNAME", username.c_str(), 1)) fail("setenv('USERNAME') failed");
      if (setenv("LOGNAME", username.c_str(), 1)) fail("setenv('LOGNAME') failed");
      if (setenv("SHELL", shell.c_str(), 1)) fail("setenv('SHELL') failed");
      if (setenv("HOME", homedir.c_str(), 1)) fail("setenv('HOME') failed");
      if (setenv("LANG", "en_US.UTF-8", 1)) fail("setenv('LANG') failed");
      if (setenv("LANGUAGE", "en_US.UTF-8", 1)) fail("setenv('LANGUAGE') failed");
    case ENV_SIMPLE:
      if (setenv("IFS", " ", 1)) fail("setenv('IFS') failed");
      if (setenv("PWD", work_dir.c_str(), 1)) fail("setenv('PWD') failed");
      if (setenv("PATH", "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", 1)) fail("setenv('PATH') failed");
    case ENV_COPY:
    case ENV_EMPTY:
      ;
  }
  for (map<string, string>::const_iterator i=env_add.begin(); i!=env_add.end(); i++)
    if (setenv(i->first.c_str(), i->second.c_str(), 1))
      fail("setenv('%s') failed", i->first.c_str());
  for (set<string>::const_iterator i=env_del.begin(); i!=env_del.end(); i++)
    if (unsetenv(i->c_str()))
      fail("unsetenv('%s') failed", i->c_str());

  set_rlimit("CORE", RLIMIT_CORE, 0);

  if (memory_space > 0)
  {
    set_rlimit("AS", RLIMIT_AS, memory_space);
    set_rlimit("DATA", RLIMIT_DATA, memory_space);
    set_rlimit("STACK", RLIMIT_STACK, memory_space);
    set_rlimit("RSS", RLIMIT_RSS, memory_space);
  }
  if (stack_space > 0)
    set_rlimit("STACK", RLIMIT_STACK, min(stack_space, memory_space));
  if (data_space > 0)
    set_rlimit("DATA", RLIMIT_DATA, min(data_space, memory_space));


  if (priority > 0)
    if (setpriority(PRIO_PGRP, 0, 19-priority))
      fail("setpriority(%d) failed", 19-priority);

  if (scheduler_cpu.size())
  {
    cpu_set_t *cpusetp;
    size_t cpusets = 1 + *max_element(scheduler_cpu.begin(), scheduler_cpu.end());
    if (!(cpusetp = CPU_ALLOC(cpusets)))
      fail("cpu_alloc(%d) failed", (int)cpusets);
    cpusets = CPU_ALLOC_SIZE(cpusets);
    CPU_ZERO_S(cpusets, cpusetp);
    for (set<int>::const_iterator i = scheduler_cpu.begin(); i != scheduler_cpu.end(); i++)
      CPU_SET_S(*i, cpusets, cpusetp);
    if (sched_setaffinity(0, cpusets, cpusetp))
      fail("setaffinity failed");
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
      fail("setscheduler failed");
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
      fail("dup2(stdin) failed");
  }
  else
    if(input != "") close(0);
  if (fo >= 0)
  {
    if (dup2(fo, 1) < 0)
      fail("dup2(stdout) failed");
  }
  else
    if(output != "") close(1);
  if (fe >= 0)
  {
    if (dup2(fe, 2) < 0)
      fail("dup2(stderr) failed");
  }
  else
    if(error != "") close(2);

  for (int f=getdtablesize(); f >= 3; f--)
    if(f != debfd)
      close(f);
  if (descriptor_count > 0)
    set_rlimit("DESCRIPTORS", RLIMIT_NOFILE, descriptor_count);

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

  if(search_path)
    execvp(exec.c_str(), argv);
  else
    execv(exec.c_str(), argv);
  fail("execv('%s') failed", exec.c_str());
}

void Runner::run_parent()
{
  debug("spawn child %d", (int)child);
  runners[child] = this;
  close(pipefd[1]);
  close(pipefd[0]);
  if (!ptrace)
    offspring.insert(child);

  timespec ts;
  if (clock_gettime(CLOCK_REALTIME, &ts)) fail("clock_gettime(CLOCK_REALTIME) failed");
  start_time = miliseconds(ts);
}

void Runner::process_child()
{
  int status;
  rusage usage;
  if (!check_times())
    return;
  pid_t p = wait4(-1 * child, &status, WNOHANG | WUNTRACED, &usage);
  if (p < 0)
    fail("wait4 failed");
  if (p == 0)
    return;
  if (offspring.find(p) == offspring.end())
  {
    if (ptrace)
    {
//    ::ptrace(PTRACE_ATTACH, p, NULL, NULL);
      ::ptrace(PTRACE_SETOPTIONS, p, NULL, PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT);
    }
    offspring.insert(p);
    runners[p] = this;
  }
  bool force_stop = false;
  if (WIFEXITED(status) || WIFSIGNALED(status))
  {
    if(WIFEXITED(status))
      debug("Exited %d", (int)p);
    if(WIFSIGNALED(status))
    {
      int s = WSTOPSIG(status);
      debug("Signaled %d (%d)", (int)p, s);
    }
    dead_pids_time.first += miliseconds(usage).first;
    dead_pids_time.second += miliseconds(usage).second;
    offspring.erase(p);
    runners.erase(p);
    if (p == child)
    {
      result.exit_status = status;
      result.usage = usage;
      if(!check_times())
        return;
      if ((memory_space > 0 && usage.ru_maxrss > memory_space))
        result.status = RES_MEMORY;
      else if (WIFEXITED(status) && (WEXITSTATUS(status) == 0))
        result.status = RES_OK;
      else
        result.status = RES_RUNTIME;
      Stop();
    }
  }
  else if (WIFSTOPPED(status))
  {
    if (ptrace)
    {
      siginfo_t sigi;
      ::ptrace(PTRACE_GETSIGINFO, p, NULL, &sigi);
      int sig = sigi.si_signo;
      //t sig = WSTOPSIG(status);

      if (sig == SIGTRAP)
      {
        user_regs_struct regs;
        ::ptrace(PTRACE_GETREGS, p, NULL, &regs);
        switch (regs.orig_rax)
        {
          case __NR_execve:
            if(!after_exec)
            {
              timespec ts;
              before_exec_time = miliseconds(usage);
              if (clock_gettime(CLOCK_REALTIME, &ts)) fail("clock_gettime(CLOCK_REALTIME) failed");
              start_time = miliseconds(ts);
            }
            else if (ptrace_safe)
            {
              result.status = RES_IO;
              Stop();
            }
            after_exec = true;
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
          default:
            if (ptrace_safe)
            {
              result.status = RES_IO;
              Stop();
            }
          //TODO: Handle syscalls!
        }
        debug("Syscall %d %d", (int)p, (int)regs.orig_rax);
        ::ptrace(PTRACE_SETREGS, p, NULL, &regs);
        ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
      }
      else if ((sig == (SIGTRAP | (PTRACE_EVENT_FORK << 8))) ||
          (sig == (SIGTRAP | (PTRACE_EVENT_VFORK << 8))) ||
          (sig == (SIGTRAP | (PTRACE_EVENT_CLONE << 8)))
         )
      {
        //TODO: Handle new child? No need?
        unsigned long npid;
        ::ptrace(PTRACE_GETEVENTMSG, p, NULL, &npid);
        debug("-> Thread %d %lu", (int)p, npid);
        ::ptrace(PTRACE_ATTACH, npid, NULL, NULL);
        ::ptrace(PTRACE_SETOPTIONS, npid, NULL, PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT);
        ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
        debug("<- Thread %d %lu", (int)p, npid);
      }
      else if (sig == (SIGTRAP | (PTRACE_EVENT_EXEC << 8)))
      {
        //TODO: Allow him to exec?
        debug("-> Execing %d", (int)p);
        ::ptrace(PTRACE_ATTACH, p, NULL, NULL);
        ::ptrace(PTRACE_SETOPTIONS, p, NULL, PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK | PTRACE_O_TRACECLONE | PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT);
        ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
        debug("<- Execing %d", (int)p);
      }
      else if (sig == (SIGTRAP | (PTRACE_EVENT_EXIT << 8)))
      {
        unsigned long exit_status;
        ::ptrace(PTRACE_GETEVENTMSG, p, NULL, &exit_status);
        debug("-> Exiting %d %lu", (int)p, exit_status);
        //TODO: Check something on exit?
        ::ptrace(PTRACE_SYSCALL, p, NULL, NULL);
        debug("<- Exiting %d %lu", (int)p, exit_status);
      }
      else
        force_stop = true;
    }
    else
      force_stop = true;
  }
  else
    force_stop = true;
  if (p==child && force_stop)
  {
    debug("Child stoped for unknown reason");
    result.status = RES_RUNTIME;
    Stop();
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
  controller_host = "www.onet.pl";
  controller_port = 80;
  map<string, string> input, output;
  input["hello"] = "world";
//input["hello2"] = "world2";
  contact_controller("index.php", input, output);
  string yaml;
  dump_yaml(output, yaml);
  debug("Contact result: %s", yaml.c_str());
  exit(1);
  if (debug_file != "")
    if ((debug_file != "") && ((debfd = open(debug_file.c_str(), O_WRONLY|O_CREAT|O_APPEND, 0644)) < 0))
      fail("open('%s') failed", debug_file.c_str());
  if (ptrace_safe)
    ptrace = true;
  if (user == "" && thread_count > 0)
    debug("BEWARE! 'thread_count' sets limits for user, not for process group!");
  if (child > 0)
    fail("run failed");
  if (pipe(pipefd))
    fail("pipe failed");
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
  void *childstack, *stack = malloc(getpagesize());
  if (!stack)
    fail("child stack malloc failed");

  childstack = (void*)((char*)stack + getpagesize());
  child = clone(child_runner, childstack, flags, (void*)this);
  if (child > 0)
    run_parent();
  else
    fail("clone failed");
}

void Runner::Stop()
{
  if (child > 0)
  {
    if (result.status == RES_OTHER)
      result.status = RES_STOP;
    killpg(child, SIGKILL);
    runners.erase(child);
    for (set<long>::const_iterator i = offspring.begin(); i != offspring.end(); i++)
      runners.erase(*i);
    offspring.clear();
    child=-1;
  }
}

void Runner::Wait()
{
  while (child>0 && check_times())
    milisleep(250);
}
