"""Heartbeat watcher: prints HUTIAN_WAKE when a further chunk (all 24 configs) of the logits matrix is complete."""
import os, sys, time, glob
d = sys.argv[1]; wake_at = [int(x) for x in sys.argv[2].split(",")]; done = set()
while True:
    n = 0
    while all(os.path.exists(f"{d}/{k:02d}__c{n}.npy") for k in range(24)): n += 1
    for w in wake_at:
        if n >= w and w not in done: done.add(w); print(f"HUTIAN_WAKE complete chunks: {n}", flush=True)
    print(f"HUTIAN_PROGRESS {time.strftime('%H:%M:%S')} complete_chunks={n} files={len(glob.glob(d + '/*.npy'))}", flush=True)
    if len(done) == len(wake_at): break
    time.sleep(600)
