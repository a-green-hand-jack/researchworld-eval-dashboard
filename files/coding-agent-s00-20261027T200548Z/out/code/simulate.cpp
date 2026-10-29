#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <vector>
// Input: graph count, then n m trials seed and m undirected edges per graph.
// Output: one line of uncensored cover times per graph; initial vertex costs 0.
int main(int argc, char** argv) {
  if (argc != 3) return 2;
  std::ifstream in(argv[1]); std::ofstream out(argv[2]);
  int graphs; if (!(in >> graphs)) return 3;
  for (int g=0; g<graphs; ++g) {
    int n,m,trials; uint64_t seed; in >> n >> m >> trials >> seed;
    if(n<2 || n>30) return 4;
    std::vector<std::vector<int>> a(n);
    for(int j=0,u,v;j<m;++j){in>>u>>v;a[u].push_back(v);a[v].push_back(u);}
    std::mt19937_64 rng(seed);
    std::vector<std::uniform_int_distribution<int>> next;
    for(auto &v:a){if(v.empty())return 5;next.emplace_back(0,v.size()-1);}
    std::uniform_int_distribution<int> start(0,n-1);
    const uint32_t full=(uint32_t(1)<<n)-1;
    for(int r=0;r<trials;++r){
      int v=start(rng); uint32_t seen=uint32_t(1)<<v; uint64_t t=0;
      while(seen!=full){v=a[v][next[v](rng)];seen|=uint32_t(1)<<v;++t;}
      out<<t<<(r+1==trials?'\n':' ');
    }
  }
  return in && out ? 0 : 6;
}
