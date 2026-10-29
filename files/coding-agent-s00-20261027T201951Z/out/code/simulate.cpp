#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>
// Each graph has an independent RNG stream; no walk truncation.
int main(int argc, char** argv) {
 if(argc!=4) return 2;
 std::ifstream in(argv[1]); std::ofstream out(argv[2]);
 int count, trials=std::stoi(argv[3]); in>>count;
 for(int g=0;g<count;++g){
  int n,m; uint64_t seed; in>>n>>m>>seed;
  if(n<2 || n>30) return 3;
  std::vector<std::vector<int>> adj(n);
  for(int i=0,a,b;i<m;++i){in>>a>>b;adj[a].push_back(b);adj[b].push_back(a);}
  std::mt19937_64 rng(seed);
  std::uniform_int_distribution<int> start(0,n-1);
  std::vector<std::uniform_int_distribution<int>> next;
  for(auto& a:adj){if(a.empty())return 4;next.emplace_back(0,a.size()-1);}
  for(int t=0;t<trials;++t){
   int v=start(rng); uint32_t seen=uint32_t(1)<<v;
   const uint32_t full=(uint32_t(1)<<n)-1; uint64_t steps=0;
   while(seen!=full){v=adj[v][next[v](rng)];seen|=uint32_t(1)<<v;++steps;}
   if(t)out<<',';out<<steps;
  }
  out<<'\n';
 }
 return !in || !out;
}
