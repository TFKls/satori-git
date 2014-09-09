// vim:ts=4:sts=4:sw=4:expandtab
#include <cassert>
#include <cerrno>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>

#include <curl/curl.h>
#include <popt.h>

#include "runner.h"

using namespace std;
using namespace runner;

/* program version */
#ifndef VERSION
#error VERSION not defined!
#endif

#define str(x) #x
#define STR(x) str(x)

enum { OPT_NONE, OPT_VERSION, OPT_HELP };

vector<string> explode(string s, char c) {
    vector<string> ret;
    size_t p=0;
    for(size_t i=0;i<s.length();i++)
        if(s[i]==c) {
            ret.push_back(s.substr(p,i-p));
            p=i+1;
        }
    if(p<s.length())
        ret.push_back(s.substr(p));
    return ret;
}

static struct poptOption PSEUDO_OPT[] = {
    { "version",  'V',  POPT_ARG_NONE,  NULL, OPT_VERSION,  "print version information end exit", NULL },
    { "help",     '?',  POPT_ARG_NONE,  NULL, OPT_HELP,     "print this help message and exit",   NULL },
    POPT_TABLEEND
};

static struct {
    char*   root_dir;
    char*   work_dir;
    char*   user;
    char*   group;
    char*   env;
    char*   env_add;
    long    priority;
    char*   stdin;
    char*   stdout;
    int     stdout_trunc;
    char*   stderr;
    int     stderr_trunc;
    long    cpu_count;
    double  real_time;
    double  cpu_time;
    long    memory;
    long    stack;
    long    files;
    char*   control_host;
    char*   control_group;
    char*   control_session;
    char*   control_secret;
    char*   log_level;
    char*   log_file;
    char**  argv;
} config;

static struct poptOption CONFIG_OPT[] = {
    { "root-dir",        0,   POPT_ARG_STRING, &config.root_dir,       0, "run the child in the root directory DIR",            "DIR" },
    { "work-dir",        0,   POPT_ARG_STRING, &config.work_dir,       0, "set the working directory to DIR (inside chroot)",   "DIR" },
    { "user",            0,   POPT_ARG_STRING, &config.user,           0, "run with effective user name NAME",                  "NAME" },
    { "group",           0,   POPT_ARG_STRING, &config.group,          0, "run with effective group name NAME",                 "NAME" },
    { "env",             0,   POPT_ARG_STRING, &config.env,            0, "set environment content to LEVEL ('empty', 'simple', 'full', 'copy')", "LEVEL" },
    { "env-add",         0,   POPT_ARG_STRING, &config.env_add,        0, "add environment constants from LIST",                "LIST" },
    { "priority",        0,   POPT_ARG_LONG,   &config.priority,       0, "set process priority to PRIO",                       "PRIO" },
    { "stdin",           0,   POPT_ARG_STRING, &config.stdin,          0, "redirect standard input from FILE",                  "FILE" },
    { "stdout",          0,   POPT_ARG_STRING, &config.stdout,         0, "redirect standard output to FILE",                   "FILE" },
    { "trunc-stdout",    0,   POPT_ARG_NONE,   &config.stdout_trunc,   0, "truncate standard output",                           0 },
    { "stderr",          0,   POPT_ARG_STRING, &config.stderr,         0, "redirect standard error output to FILE",             "FILE" },
    { "trunc-stderr",    0,   POPT_ARG_NONE,   &config.stderr_trunc,   0, "truncate standard error",                            0 },
    { "max-cpus",        0,   POPT_ARG_STRING, &config.cpu_count,      0, "limit cpu usage to LIMIT processors",                "LIMIT" },
    { "max-real-time",   0,   POPT_ARG_DOUBLE, &config.real_time,      0, "limit real time to LIMIT seconds",                   "LIMIT" },
    { "max-cpu-time",    0,   POPT_ARG_DOUBLE, &config.cpu_time,       0, "limit CPU time to LIMIT seconds",                    "LIMIT" },
    { "max-memory",      0,   POPT_ARG_LONG,   &config.memory,         0, "limit memory usage to LIMIT bytes",                  "LIMIT" },
    { "max-stack",       0,   POPT_ARG_LONG,   &config.stack,          0, "limit stack usage to LIMIT bytes",                   "LIMIT" },
    { "max-files",       0,   POPT_ARG_LONG,   &config.files,          0, "limit open file count to LIMIT",                     "LIMIT" },
    { "control-host",    0,   POPT_ARG_STRING, &config.control_host,   0, "set satori_rund host HOST[:PORT]",                   "HOST" },
    { "control-group",   0,   POPT_ARG_STRING, &config.control_group,  0, "set control group NAME",                             "NAME" },
    { "log-level",       0,   POPT_ARG_STRING, &config.log_level,      0, "set logging verbosity to LEVEL ('debug', 'warning', 'error', 'critical', 'none')", "LEVEL" },
    { "log-file",        0,   POPT_ARG_STRING, &config.log_file,       0, "file for logging information",                       "FILE" },
    POPT_TABLEEND
};
static struct poptOption options[] = {
    { NULL, 0, POPT_ARG_INCLUDE_TABLE, CONFIG_OPT, 0, "Program execution options:", NULL },
    { NULL, 0, POPT_ARG_INCLUDE_TABLE, PSEUDO_OPT, 0, "Other operations:",          NULL },
    POPT_TABLEEND
};

const char* NOTHING = NULL;
void parse_options(int argc, const char* argv[]) {
    memset(&config, 0, sizeof(config));
    poptContext ctx = poptGetContext(NULL, argc, argv, options, POPT_CONTEXT_POSIXMEHARDER);
    poptSetOtherOptionHelp(ctx, "[options] <executable> <arguments>");
    int rc;
    if ((rc=poptGetNextOpt(ctx)) != -1) {
        switch (rc) {
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
    argv = poptGetArgs(ctx);
    if (!argv) argv = &NOTHING;
    for (argc=0; argv[argc]; ++argc);
    config.argv = (char**) malloc((argc+1) * sizeof(char*));
    for (argc=0; argv[argc]; ++argc)
        config.argv[argc] = strdup(argv[argc]);
    config.argv[argc] = NULL;
    if (!config.argv[0]) {
        poptPrintHelp(ctx, stderr, 0);
        exit(1);
    }
    poptFreeContext(ctx);
    if (not config.control_host)
        config.control_host = getenv("SATORI_RUND");
    config.control_session = getenv("SATORI_RUND_SESSION");
    config.control_secret = getenv("SATORI_RUND_SECRET");
}

Runner run;

int finish() {
    printf("Result       : ");
    switch (run.result.status) {
        case Result::RES_OK: printf("OK\n"); break;
        case Result::RES_TIME: printf("TLE\n"); break;
        case Result::RES_MEMORY: printf("MEM\n"); break;
        case Result::RES_RUNTIME: printf("RTE\n"); break;
        case Result::RES_STOP: printf("STP\n"); break;
        case Result::RES_FAIL: printf("FLD\n"); break;
        default: printf("UNK\n");
    }
    printf("Return       : %d\n", WEXITSTATUS(run.result.exit_status));
    printf("Memory       : %llu\n", run.result.memory);
    printf("CPU          : %lf\n", run.result.cpu_time);
    printf("Time         : %lf\n", run.result.real_time);
    printf("Instructions : %lu\n", run.result.instructions);
    printf("Cycles       : %lu\n", run.result.cycles);
    if (run.result.status == Result::RES_OK)
        return 0;
    return 1;
}

void signalhandler(int sig, siginfo_t* info, void* data) {
    run.Stop();
    exit(finish());
}

int main(int argc, const char** argv) {
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
    if (config.root_dir)
        run.root_dir = config.root_dir;
    if (config.work_dir)
        run.work_dir = config.work_dir;
    if (config.user)
        run.user = config.user;
    if (config.group)
        run.group = config.group;
    if (config.env) {
        if (strcasecmp("empty", config.env) == 0)
            run.env_level = Runner::ENV_EMPTY;
        else if (strcasecmp("simple", config.env) == 0)
            run.env_level = Runner::ENV_SIMPLE;
        else if (strcasecmp("full", config.env) == 0)
            run.env_level = Runner::ENV_FULL;
        else if (strcasecmp("copy", config.env) == 0)
            run.env_level = Runner::ENV_COPY;
    }
    if (config.env_add) {
        vector<string> vs = explode(config.env_add, ',');
        for (uint i = 0; i < vs.size(); i++) {
            vector<string> kv = explode(vs[i], '=');
            if(kv.size() == 2)
                run.env_add[kv[0]] = kv[1];
        }
    }
    if (config.priority > 0)
        run.priority = config.priority;
    if (config.stdin)
        run.input = config.stdin;
    if (config.stdout)
        run.output = config.stdout;
    if (config.stdout_trunc)
        run.output_trunc = true;
    if (config.stderr) {
        if (strcmp(config.stderr, "__STDOUT__") == 0)
            run.error_to_output = true;
        else
            run.error = config.stderr;
    }
    if (config.stderr_trunc)
        run.error_trunc = true;
    if (config.cpu_count > 0)
        run.cpu_count = config.cpu_count;
    if (config.real_time > 0)
        run.real_time = config.real_time;
    if (config.cpu_time > 0)
        run.cpu_time = config.cpu_time;
    if (config.memory > 0)
        run.memory_space = config.memory;
    if (config.stack > 0)
        run.stack_space = config.stack;
    if (config.files > 0)
        run.descriptor_count = config.files;
    if (config.log_level) {
        if (strcasecmp("debug", config.log_level) == 0)
            Logger::SetLevel(Logger::DEBUG);
        if (strcasecmp("warning", config.log_level) == 0)
            Logger::SetLevel(Logger::WARNING);
        if (strcasecmp("error", config.log_level) == 0)
            Logger::SetLevel(Logger::ERROR);
        if (strcasecmp("critical", config.log_level) == 0)
            Logger::SetLevel(Logger::CRITICAL);
        if (strcasecmp("none", config.log_level) == 0)
            Logger::SetLevel(Logger::NONE);
    }
    if (config.log_file)
        run.log_file = config.log_file;

    string control_host("localhost");
    if (config.control_host)
        control_host = config.control_host;
    control_host += ":8765";
    run.control_host = explode(control_host, ':')[0];
    run.control_port = atoi(explode(control_host, ':')[1].c_str());
    if (config.control_session)
        run.control_session = config.control_session;
    if (config.control_secret)
        run.control_secret = config.control_secret;
    if (config.control_group)
        run.cgroup = config.control_group;

    run.exec = config.argv[0];
    for (uint i = 1; config.argv[i]; i++)
        run.params.push_back(config.argv[i]);

    run.search_path = true;
    run.cap_level = Runner::CAP_EMPTY;
    run.env_del.insert("SATORI_RUND_SECRET");
    run.env_del.insert("SATORI_RUND_SESSION");

    run.Run();
    run.Wait();
    run.Stop();

    int res = finish();
    curl_global_cleanup();
    return res;
}
