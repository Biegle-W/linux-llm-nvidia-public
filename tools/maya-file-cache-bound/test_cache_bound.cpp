#include "bounded_file_cache.hpp"
#include <cassert>
#include <cstring>
#include <string>
int main(int argc, char** argv) {
    assert(argc == 2);
    std::string pattern = std::string(argv[1]) + "/cache-test-XXXXXX";
    std::vector<char> name(pattern.begin(), pattern.end()); name.push_back(0);
    int fd = mkstemp(name.data()); assert(fd >= 0);
    constexpr size_t bytes = 32UL << 20;
    std::vector<unsigned char> data(1UL << 20, 71);
    for (size_t i = 0; i < bytes; i += data.size()) assert(write(fd, data.data(), data.size()) == (ssize_t)data.size());
    assert(fdatasync(fd) == 0);
    auto* p = (unsigned char*)mmap(nullptr, bytes, PROT_READ, MAP_SHARED, fd, 0); assert(p != MAP_FAILED);
    volatile uint64_t total = 0;
    for (size_t i = 0; i < bytes; i += 4096) total = total + p[i];
    maya_cache_bound::Controller controller({{p, bytes, fd, 0}}, 4UL << 20, 1UL << 20);
    auto result = controller.sweep();
    assert(result.errors == 0 && result.before >= bytes && result.after <= (4UL << 20));
    assert(result.discarded >= (28UL << 20));
    controller.start();
    for (int n = 0; n < 3; ++n) {
        for (size_t i = 0; i < bytes; i += 4096) assert(p[i] == 71);
        std::this_thread::sleep_for(std::chrono::milliseconds(250));
    }
    controller.stop();
    for (size_t i = 0; i < bytes; i += 4096) assert(p[i] == 71);
    munmap(p, bytes); close(fd); unlink(name.data());
    std::puts("PASS: clean-page eviction, concurrent rereads, unchanged data and joined shutdown");
}
