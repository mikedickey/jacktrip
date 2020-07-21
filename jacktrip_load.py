#!/usr/bin/python3

import re
import time
import copy
import argparse
import subprocess
from multiprocessing import Pool

def parse_args():
    parser = argparse.ArgumentParser(description="Spawns JackTrip client processes to test a hubpatch server")
    parser.add_argument("--count", type=int, default=1, help="Number of JackTrip client processes to spawn")
    parser.add_argument("--server", type=str, default=None, help="Hostname or IP address of JackTrip server")
    parser.add_argument("--port", type=int, default=4464, help="Port number of JackTrip server")
    parser.add_argument("--exe", type=str, default="jacktrip", help="JackTrip client executable")
    parser.add_argument("--sleep", type=int, default=0, help="Seconds to sleep in between each client")
    args, extra_args = parser.parse_known_args()
    args.extra_args = extra_args
    if not args.server:
        print("No server specified, using localhost")
        args.server = "localhost"
    return args

def main():
    args = parse_args()
    spawn_clients(args)

def spawn_clients(args):
    jacktrip_args = [args.exe, "-C", args.server, "--peerport", str(args.port)]
    if args.extra_args and args.extra_args != "":
        jacktrip_args.extend(args.extra_args)
    pool = Pool(processes=args.count)
    for x in range(0, args.count):
        result = pool.apply_async(run_client, [x, jacktrip_args])
        if args.sleep > 0:
            time.sleep(args.sleep)
    pool.close()
    pool.join()

def run_client(id, jacktrip_args):
    my_args = copy.deepcopy(jacktrip_args)
    my_args.extend(["--bindport", str(4474+id)])
    cmd = " ".join(my_args)
    print(f'Client #{id} is starting: {cmd}')
    p = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    waiting_for_peer = re.compile(".*Waiting.for.Peer.*")
    received_connection = re.compile(".*Received.Connection.from.Peer.*")
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if waiting_for_peer.match(line):
            print(f'Client #{id} is waiting for peer')
        elif received_connection.match(line):
            print(f'Client #{id} received connection from peer')
    retcode = p.wait()
    print(f'Client #{id} return code={retcode}')

if __name__ == '__main__':
    main()
