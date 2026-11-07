"""Record whole-command wall/CPU/RSS without changing the command's behavior."""
import argparse,datetime,hashlib,json,os,pathlib,resource,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--record',required=True);p.add_argument('command',nargs=argparse.REMAINDER);args=p.parse_args()
command=args.command[1:] if args.command[:1]==['--'] else args.command
assert command
started=datetime.datetime.now(datetime.timezone.utc).isoformat();wall=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN)
code=subprocess.call(command);after=resource.getrusage(resource.RUSAGE_CHILDREN)
record={'command':command,'cwd':str(pathlib.Path.cwd()),'started_utc':started,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'elapsed_seconds':time.perf_counter()-wall,'child_user_cpu_seconds':after.ru_utime-before.ru_utime,'child_system_cpu_seconds':after.ru_stime-before.ru_stime,
 'peak_child_rss_kib':after.ru_maxrss,'exit_code':code,'thread_environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']},
 'wrapper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
 'timing_scope':'Full child command including loading, validation, cache reads, fitting/prediction and writing; CPU excludes world suspension; wall can include it'}
path=pathlib.Path(args.record);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print('HUTIAN_WAKE: measured command ended '+str(path)+' exit '+str(code),flush=True)
raise SystemExit(code)
