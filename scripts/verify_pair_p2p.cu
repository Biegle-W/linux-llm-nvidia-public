#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <cstring>
#define CK(x) do {cudaError_t e=(x);if(e!=cudaSuccess){fprintf(stderr,"%s: %s\n",#x,cudaGetErrorString(e));exit(1);}}while(0)
__global__ void copy_remote(unsigned* dst,const unsigned* src,size_t n){size_t i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)dst[i]=src[i];}
int main(){
 int n;CK(cudaGetDeviceCount(&n)); int a=-1,b=-1;
 for(int i=0;i<n;i++){cudaDeviceProp p;CK(cudaGetDeviceProperties(&p,i));printf("GPU%d %s\n",i,p.name);if(strstr(p.name,"3080 Ti"))a=i;else if(strstr(p.name,"3080"))b=i;}
 if(a<0||b<0){fprintf(stderr,"Required 3080 pair absent\n");return 2;}
 for(int dir=0;dir<2;dir++){
  int s=dir?b:a,d=dir?a:b,can;CK(cudaDeviceCanAccessPeer(&can,d,s));printf("GPU%d accesses GPU%d: %d\n",d,s,can);if(!can)return 3;
  CK(cudaSetDevice(d));CK(cudaDeviceEnablePeerAccess(s,0));
  const size_t count=4*1024*1024,bytes=count*sizeof(unsigned);unsigned *src,*dst;std::vector<unsigned> h(count),out(count);
  CK(cudaSetDevice(s));CK(cudaDeviceEnablePeerAccess(d,0));CK(cudaMalloc(&src,bytes));CK(cudaSetDevice(d));CK(cudaMalloc(&dst,bytes));
  for(unsigned seed=1;seed<=3;seed++){
   for(size_t i=0;i<count;i++)h[i]=(unsigned)i*2654435761u+seed;
   CK(cudaSetDevice(s));CK(cudaMemcpy(src,h.data(),bytes,cudaMemcpyHostToDevice));CK(cudaSetDevice(d));
   CK(cudaMemset(dst,0,bytes));copy_remote<<<(count+255)/256,256>>>(dst,src,count);CK(cudaGetLastError());CK(cudaDeviceSynchronize());
   CK(cudaMemcpy(out.data(),dst,bytes,cudaMemcpyDeviceToHost));if(out!=h){fprintf(stderr,"REMOTE READ MISMATCH\n");return 4;}
   CK(cudaSetDevice(s));CK(cudaMemset(src,0,bytes));copy_remote<<<(count+255)/256,256>>>(dst,src,count);CK(cudaGetLastError());CK(cudaDeviceSynchronize());
   CK(cudaSetDevice(d));CK(cudaMemcpy(out.data(),dst,bytes,cudaMemcpyDeviceToHost));for(unsigned v:out)if(v){fprintf(stderr,"REMOTE WRITE MISMATCH\n");return 5;}
  }
  CK(cudaSetDevice(d));cudaEvent_t start,end;CK(cudaEventCreate(&start));CK(cudaEventCreate(&end));CK(cudaEventRecord(start));
  for(int j=0;j<32;j++)CK(cudaMemcpyPeerAsync(dst,d,src,s,bytes));CK(cudaEventRecord(end));CK(cudaEventSynchronize(end));float ms;CK(cudaEventElapsedTime(&ms,start,end));
  printf("PASS GPU%d -> GPU%d remote reads/writes, 3 patterns, 16 MiB; peer copy %.3f GB/s\n",s,d,bytes*32.0/(ms*1e6));
  CK(cudaEventDestroy(start));CK(cudaEventDestroy(end));CK(cudaFree(dst));CK(cudaSetDevice(s));CK(cudaFree(src));CK(cudaDeviceDisablePeerAccess(d));CK(cudaSetDevice(d));CK(cudaDeviceDisablePeerAccess(s));
 }
 puts("PASS: both directions verified");return 0;
}
