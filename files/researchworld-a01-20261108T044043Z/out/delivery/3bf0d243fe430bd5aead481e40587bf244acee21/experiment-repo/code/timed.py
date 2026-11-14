"""Run a command and append its wall-clock and CPU time (user+sys of the process and its children) to a CSV.
Usage: python3 code/timed.py LABEL TIMES.csv -- COMMAND [ARGS...]"""
import sys, time, subprocess, resource, os
label, out = sys.argv[1], sys.argv[2]; cmd = sys.argv[sys.argv.index("--") + 1:]
r0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.time()
rc = subprocess.call(cmd)
r1 = resource.getrusage(resource.RUSAGE_CHILDREN); wall = time.time() - t0
new = not os.path.exists(out)
with open(out, "a") as f:
    if new: f.write("step,wall_s,cpu_user_s,cpu_sys_s,exit\n")
    f.write(f"{label},{wall:.1f},{r1.ru_utime - r0.ru_utime:.1f},{r1.ru_stime - r0.ru_stime:.1f},{rc}\n")
sys.exit(rc)
