"""Capture measured compute before the inference server is stopped."""
import argparse, datetime, json, os, pathlib, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);a=p.parse_args()
    proc=pathlib.Path('/proc')/str(a.pid);st=(proc/'stat').read_text().split()
    info={}
    for line in (proc/'status').read_text().splitlines():
        if line.startswith(('VmHWM:','VmRSS:','Threads:')):
            k,v=line.split(':',1);info[k]=v.strip()
    records=[json.loads(x) for x in (ROOT/'data/responses.jsonl').open()]
    dates=[datetime.datetime.strptime(x['completed_utc'],'%Y-%m-%dT%H:%M:%SZ') for x in records]
    out=dict(captured_unix=time.time(),main_server_pid=a.pid,
        main_server_cpu_seconds=(int(st[13])+int(st[14]))/os.sysconf('SC_CLK_TCK'),
        main_server_peak_rss_kib=int(info['VmHWM'].split()[0]),
        main_server_current_rss_kib=int(info['VmRSS'].split()[0]),
        main_server_threads=int(info['Threads']),
        retained_responses=len(records),generated_tokens=sum(x['tokens_predicted'] for x in records),
        total_prompt_tokens_including_cached=sum(x['tokens_evaluated'] for x in records),
        processed_prompt_tokens=sum(x['timings']['prompt_n'] for x in records),
        cached_prompt_tokens=sum(x['timings']['cache_n'] for x in records),
        retained_response_wall_span_seconds=(max(dates)-min(dates)).total_seconds(),
        notes='Server CPU/RSS excludes terminated first engineering server; wall span includes completed pilots and pauses. No GPU or inference API.')
    (ROOT/'logs/compute.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
