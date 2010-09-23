#include <cassert>
#include <cerrno>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>

#include <string>
#include <vector>

#include <popt.h>

#include <curl/curl.h>

#include "runner.h"

using namespace std;

/* program version */
#ifndef VERSION
#error VERSION not defined!
#endif

#define str(x) #x
#define STR(x) str(x)

enum { OPT_NONE, OPT_VERSION, OPT_HELP };

vector<string> explode(string s, char c)
{
  vector<string> ret;
  size_t p=0;
  for(size_t i=0;i<s.length();i++)
    if(s[i]==c)
    {
      ret.push_back(s.substr(p,i-p));
      p=i+1;
    }
  if(p<s.length())
    ret.push_back(s.substr(p));
  return ret;
}

static struct poptOption PSEUDO_OPT[] =
{
  { "version",  'V',  POPT_ARG_NONE,  NULL, OPT_VERSION,  "print version information end exit", NULL },
  { "help",     '?',  POPT_ARG_NONE,  NULL, OPT_HELP,     "print this help message and exit",   NULL },
  POPT_TABLEEND
};

static struct
{
  const char*   debug;
  const char*   chroot;
  int           pivot;
  char* const*  argv;
  const char*   workdir;
  const char*   stdin;
  const char*   stdout;
  int           stdouttrunc;
  const char*   stderr;
  int           stderrtrunc;
  const char*   setuid;
  const char*   setgid;
  int           ptrace;
  int           memlock;
  int           iotrace;
  const char*   env_level;
  const char*   env_add;
  const char*   env_del;
  const char*   cap_level;
  const char*   affinity;
  long          threads;
  long          realtime;
  long          cputime;
  long          usrtime;
  long          systime;
  long          memory;
  long          stack;
  long          data;
  long          files;
  long          io_read;
  long          io_write;
  long          priority;
  int           quiet;
  int           search;
  int           ns_ipc;
  int           ns_net;
  int           ns_mount;
  int           mount_proc;
  int           ns_pid;
  int           ns_uts;
  const char*   c_host;
  long          c_port;
  const char*   c_group;
  long          c_memory;
  long          c_cputime;
  long          c_usrtime;
  long          c_systime;
} config;

static struct poptOption CONFIG_OPT[] =
{
  { "debug",           0,   POPT_ARG_STRING, &config.debug,          0, "file for debug information",                         "DIR" },
  { "root",            0,   POPT_ARG_STRING, &config.chroot,         0, "run the child with the root directory DIR",          "DIR" },
  { "pivot",           0,   POPT_ARG_NONE,   &config.pivot,          0, "use pivot instead of chroot",                        0 },
  { "work-dir",        0,   POPT_ARG_STRING, &config.workdir,        0, "set the working directory to DIR (inside chroot)",   "DIR" },
  { "stdin",           0,   POPT_ARG_STRING, &config.stdin,          0, "redirect standard input from FILE",                  "FILE" },
  { "stdout",          0,   POPT_ARG_STRING, &config.stdout,         0, "redirect standard output to FILE",                   "FILE" },
  { "stderr",          0,   POPT_ARG_STRING, &config.stderr,         0, "redirect standard error output to FILE",             "FILE" },
  { "trunc-stdout",    0,   POPT_ARG_NONE,   &config.stdouttrunc,    0, "truncate standard output",                           0 },
  { "trunc-stderr",    0,   POPT_ARG_NONE,   &config.stderrtrunc,    0, "truncate standard error",                            0 },
  { "setuid",          0,   POPT_ARG_STRING, &config.setuid,         0, "run with effective user name NAME",                  "NAME" },
  { "setgid",          0,   POPT_ARG_STRING, &config.setgid,         0, "run with effective group name NAME",                 "NAME" },
  { "cpus",            0,   POPT_ARG_STRING, &config.affinity,       0, "bind execution to processors from LIST",             "LIST" },
  { "max-threads",     0,   POPT_ARG_LONG,   &config.threads,        0, "limit the number of threads to LIMIT",               "LIMIT" },
  { "max-realtime",    0,   POPT_ARG_LONG,   &config.realtime,       0, "limit real (wall clock) time to LIMIT/1000 seconds", "LIMIT" },
  { "max-cputime",     0,   POPT_ARG_LONG,   &config.cputime,        0, "limit CPU time to LIMIT/10000 seconds",              "LIMIT" },
  { "max-usertime",    0,   POPT_ARG_LONG,   &config.usrtime,        0, "limit user-mode CPU time to LIMIT/10000 seconds",    "LIMIT" },
  { "max-systime",     0,   POPT_ARG_LONG,   &config.systime,        0, "limit system-mode CPU time to LIMIT/10000 seconds",  "LIMIT" },
  { "max-memory",      0,   POPT_ARG_LONG,   &config.memory,         0, "limit memory usage to LIMIT bytes",                  "LIMIT" },
  { "max-stack",       0,   POPT_ARG_LONG,   &config.stack,          0, "limit stack usage to LIMIT bytes",                   "LIMIT" },
  { "max-data",        0,   POPT_ARG_LONG,   &config.data,           0, "limit data usage to LIMIT bytes",                    "LIMIT" },
  { "max-files",       0,   POPT_ARG_LONG,   &config.files,          0, "limit open file count to LIMIT",                     "LIMIT" },
  { "max-read",        0,   POPT_ARG_LONG,   &config.io_read,        0, "limit write to LIMIT bytes",                         "LIMIT" },
  { "max-write",       0,   POPT_ARG_LONG,   &config.io_write,       0, "limit read to LIMIT bytes",                          "LIMIT" },
  { "ptrace",          0,   POPT_ARG_NONE,   &config.ptrace,         0, "enable ptrace",                                      0 },
  { "iotrace",         0,   POPT_ARG_NONE,   &config.iotrace,        0, "enable iotrace",                                     0 },
  { "memlock",         0,   POPT_ARG_NONE,   &config.memlock,        0, "enable memlock",                                     0 },
  { "env",             0,   POPT_ARG_STRING, &config.env_level,      0, "set environment content to LEVEL ('empty', 'simple', 'full', 'copy')", "LEVEL" },
  { "env-add",         0,   POPT_ARG_STRING, &config.env_add,        0, "add environment constants from LIST",                "LIST" },
  { "env-del",         0,   POPT_ARG_STRING, &config.env_del,        0, "delete environment constants from LIST",             "LIST" },
  { "cap",             0,   POPT_ARG_STRING, &config.cap_level,      0, "set capabilities to LEVEL ('empty', 'safe', 'copy')", "LEVEL" },
  { "priority",        0,   POPT_ARG_LONG,   &config.priority,       0, "set process priority to PRIO",                       "PRIO" },
  { "quiet",           'q', POPT_ARG_NONE,   &config.quiet,          0, "prints only the result",                             0 },
  { "search",          0,   POPT_ARG_NONE,   &config.search,         0, "search PATH for the executable",                     0 },
  { "ns-ipc",          0,   POPT_ARG_NONE,   &config.ns_ipc,         0, "enable ipc namespace",                               0 },
  { "ns-net",          0,   POPT_ARG_NONE,   &config.ns_net,         0, "enable network namespace",                           0 },
  { "ns-mount",        0,   POPT_ARG_NONE,   &config.ns_mount,       0, "enable mount namespace",                             0 },
  { "mount-proc",      0,   POPT_ARG_NONE,   &config.mount_proc,     0, "remount proc filesystem",                            0 },
  { "ns-pid",          0,   POPT_ARG_NONE,   &config.ns_pid,         0, "enable pid namespace",                               0 },
  { "ns-uts",          0,   POPT_ARG_NONE,   &config.ns_uts,         0, "enable uts namespace",                               0 },
  { "control-host",    0,   POPT_ARG_STRING, &config.c_host,         0, "set controller host HOST",                           "HOST" },
  { "control-port",    0,   POPT_ARG_LONG,   &config.c_port,         0, "set controller port PORT",                           "PORT" },
  { "cgroup",          0,   POPT_ARG_STRING, &config.c_group,        0, "set control group GROUP",                            "GROUP" },
  { "cgroup-memory",   0,   POPT_ARG_LONG,   &config.c_memory,       0, "limit memory usage to LIMIT bytes for control group",      "LIMIT" },
  { "cgroup-cputime",  0,   POPT_ARG_LONG,   &config.c_cputime,      0, "limit CPU time to LIMIT/10000 seconds for control group",              "LIMIT" },
  { "cgroup-usertime", 0,   POPT_ARG_LONG,   &config.c_usrtime,      0, "limit user-mode CPU time to LIMIT/10000 seconds for control group",    "LIMIT" },
  { "cgroup-systime",  0,   POPT_ARG_LONG,   &config.c_systime,      0, "limit system-mode CPU time to LIMIT/10000 seconds for control group",  "LIMIT" },
  POPT_TABLEEND
};
static struct poptOption options[] =
{
  { NULL, 0, POPT_ARG_INCLUDE_TABLE, CONFIG_OPT, 0, "Program execution options:", NULL },
  { NULL, 0, POPT_ARG_INCLUDE_TABLE, PSEUDO_OPT, 0, "Other operations:",          NULL },
  POPT_TABLEEND
};

const char* NOTHING = NULL;
void parse_options(int argc, const char* argv[])
{
  memset(&config, 0, sizeof(config));
  /* set defaults */
  config.argv = (char* const*)&NOTHING;
  /* parse the command line */
  poptContext ctx = poptGetContext(NULL, argc, argv, options, POPT_CONTEXT_POSIXMEHARDER);
  poptSetOtherOptionHelp(ctx, "[options] <executable> <arguments>");
  int rc;
  if ((rc=poptGetNextOpt(ctx)) != -1)
  {
    switch (rc)
    {
      case OPT_VERSION:
        printf("%s\n", "run, version " STR(VERSION));
        exit(0);
      case OPT_HELP:
        poptPrintHelp(ctx, stdout, 0);
        exit(0);
      default:
        fprintf(stderr,"%s: %s: %s\n", argv[0], poptBadOption(ctx, 0), poptStrerror(rc));
        exit(1);
    }
  }
  /* copy arguments */
  argv = poptGetArgs(ctx);
  if (!argv) argv = &NOTHING;
  for (argc=0; argv[argc]; ++argc);
  config.argv = (char**) malloc((argc+1) * sizeof(char*));
  for (argc=0; argv[argc]; ++argc)
    ((char**)config.argv)[argc] = strdup(argv[argc]);
  ((char**)config.argv)[argc] = NULL;
  /* check for program name */
  if (!config.argv[0])
  {
    poptPrintHelp(ctx, stderr, 0);
    exit(1);
  }
  poptFreeContext(ctx);
  /**/
  if (config.c_host)
  {
    char* orig = strdup(config.c_host);
    char* tmp = strstr(orig, ":");
    if (tmp && config.c_port <= 0)
      config.c_port = atoi(tmp+1);
    if (tmp)
      *tmp = '\0';
    tmp = strstr(orig, "://");
    if (!tmp)
      tmp = orig;
    char* tmp2 = strstr(tmp, "/");
    if (tmp2)
      *tmp2 = '\0';
    config.c_host = strdup(tmp);
    free(orig);
  }
  /**/
}

Runner run;

int finish()
{
  switch (run.result.status)
  {
    case Runner::RES_OK: printf("OK\n"); break;
    case Runner::RES_TIME: printf("TLE\n"); break;
    case Runner::RES_MEMORY: printf("MEM\n"); break;
    case Runner::RES_IO: printf("IOQ\n"); break;
    case Runner::RES_ILLEGAL: printf("ILL\n"); break;
    case Runner::RES_RUNTIME: printf("RTE\n"); break;
    case Runner::RES_STOP: printf("STP\n"); break;
    case Runner::RES_FAIL: printf("FLD\n"); break;
    default: printf("UNK\n");
  }
  if (!config.quiet)
  {
    printf("Status : %d\n", run.result.exit_status);
    printf("Retcode: %d\n", WEXITSTATUS(run.result.exit_status));
    printf("Memory : %lu\n", run.result.memory);
    printf("CPU    : %lu\n", run.result.cpu_time);
    printf("Time   : %lu\n", run.result.real_time);
    printf("Read   : %lu\n", run.result.sum_read);
    printf("Write  : %lu\n", run.result.sum_write);
  }
  if (run.result.status == Runner::RES_OK)
    return 0;
  return 1;
}

void signalhandler(int sig, siginfo_t* info, void* data)
{
  run.Stop();
  exit(finish());
}

int main(int argc, const char** argv)
{
  curl_global_init(CURL_GLOBAL_ALL);

  vector<int> signals;
  signals.push_back(SIGHUP);
  signals.push_back(SIGINT);
  signals.push_back(SIGQUIT);
  signals.push_back(SIGILL);
  signals.push_back(SIGABRT);
  signals.push_back(SIGFPE);
  signals.push_back(SIGSEGV);
  signals.push_back(SIGPIPE);
  signals.push_back(SIGTERM);
  signals.push_back(SIGUSR1);
  signals.push_back(SIGUSR2);
  signals.push_back(SIGBUS);
  signals.push_back(SIGPOLL);
  signals.push_back(SIGPROF);
  signals.push_back(SIGSYS);
  signals.push_back(SIGVTALRM);
  signals.push_back(SIGXCPU);
  signals.push_back(SIGXFSZ);
  signals.push_back(SIGIO);
  signals.push_back(SIGPWR);
  struct sigaction action;
  memset(&action, 0, sizeof(action));
  action.sa_sigaction = &signalhandler;
  action.sa_flags = SA_RESTART | SA_SIGINFO;
  sigfillset(&action.sa_mask);
  for (uint i=0; i<signals.size(); i++)
    sigaction(signals[i], &action, NULL);

  parse_options(argc, argv);
  if (config.debug)
    run.debug_file = config.debug;
  if (config.chroot)
    run.dir = config.chroot;
  run.pivot = config.pivot;
  if (config.workdir)
    run.work_dir = config.workdir;
  run.exec = config.argv[0];
  for (uint i = 1; config.argv[i] != NULL; i++)
    run.params.push_back(config.argv[i]);
  if (config.stdin)
    run.input = config.stdin;
  if (config.stdout)
    run.output = config.stdout;
  if (config.stderr)
    run.error = config.stderr;
  if (config.stdouttrunc)
    run.output_trunc = true;
  if (config.stderrtrunc)
    run.error_trunc = true;
  if (config.threads > 0)
    run.thread_count = config.threads;
  if (config.setuid > 0)
    run.user = config.setuid;
  if (config.setgid > 0)
    run.group = config.setgid;
  if (config.ptrace)
    run.ptrace = true;
  if (config.memlock)
    run.lock_memory = true;
  if (config.iotrace)
    run.collect_read_write_files = true;
  if (config.env_level)
  {
    if (strcasecmp("empty", config.env_level) == 0)
      run.env_level = Runner::ENV_EMPTY;
    else if (strcasecmp("simple", config.env_level) == 0)
      run.env_level = Runner::ENV_SIMPLE;
    else if (strcasecmp("full", config.env_level) == 0)
      run.env_level = Runner::ENV_FULL;
    else if (strcasecmp("copy", config.env_level) == 0)
      run.env_level = Runner::ENV_COPY;
  }
  if (config.cap_level)
  {
    if (strcasecmp("empty", config.cap_level) == 0)
      run.cap_level = Runner::CAP_EMPTY;
    else if (strcasecmp("safe", config.cap_level) == 0)
      run.cap_level = Runner::CAP_SAFE;
    else if (strcasecmp("copy", config.cap_level) == 0)
      run.cap_level = Runner::CAP_COPY;
    else if (strcasecmp("full", config.cap_level) == 0)
      run.cap_level = Runner::CAP_FULL;
  }

  if (config.cputime > 0)
    run.cpu_time = config.cputime;
  if (config.usrtime > 0)
    run.user_time = config.usrtime;
  if (config.systime > 0)
    run.system_time = config.systime;
  if (config.realtime > 0)
    run.real_time = config.realtime;
  if (config.memory > 0)
    run.memory_space = config.memory;
  if (config.stack > 0)
    run.stack_space = config.stack;
  if (config.data > 0)
    run.data_space = config.data;
  if (config.files > 0)
    run.descriptor_count = config.files;
  if (config.io_read > 0)
    run.sum_read = config.io_read;
  if (config.io_write > 0)
    run.sum_write = config.io_write;
  if (config.priority > 0)
    run.priority = config.priority;
  if (config.env_add)
  {
    vector<string> vs = explode(config.env_add, ',');
    for (uint i = 0; i < vs.size(); i++)
    {
      vector<string> kv = explode(vs[i], '=');
      if(kv.size() == 2)
        run.env_add[kv[0]] = kv[1];
    }
  }
  if (config.env_del)
  {
    vector<string> vs = explode(config.env_del, ',');
    for (uint i = 0; i < vs.size(); i++)
      run.env_del.insert(vs[i]);
  }
  if (config.affinity)
  {
    vector<string> vs = explode(config.affinity, ',');
    for (uint i = 0; i < vs.size(); i++)
      run.scheduler_cpu.insert(atoi(vs[i].c_str()));
  }
  run.search_path = config.search;
  run.new_ipc = config.ns_ipc;
  run.new_net = config.ns_net;
  run.new_mount = config.ns_mount;
  run.mount_proc = config.mount_proc;
  run.new_pid = config.ns_pid;
  run.new_uts = config.ns_uts;
  if (config.c_group)
    run.cgroup = config.c_group;
  if (config.c_host)
    run.controller_host = config.c_host;
  if (config.c_port)
    run.controller_port = config.c_port;
  if (config.c_memory > 0)
    run.cgroup_memory = config.c_memory;
  if (config.c_cputime > 0)
    run.cgroup_time = config.c_cputime;
  if (config.c_usrtime > 0)
    run.cgroup_user_time = config.c_usrtime;
  if (config.c_systime > 0)
    run.cgroup_system_time = config.c_systime;


  run.Run();
  run.Wait();
  run.Stop();
  int res = finish();
  curl_global_cleanup();
  return res;
}
