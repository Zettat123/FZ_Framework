# FZ IoT Framework

## Prerequisites

### 1. Docker
- Version 17.06 (Other versions may work but have not been tested)
- Please run `docker run hello-world` to check Docker has been installed successfully.

### 2. CRIU
- Version 3.14 (Other versions may work but have not been tested)
- Check the kernel options have been enabled according to [Linux kernel](https://www.criu.org/Linux_kernel). The kernel should be rebuilt if some options were disabled.
- Please run `criu check` as superuser to check CRIU has been installed successfully. Notice that CRIU commands may fail because of other reasons though the check command outputs "Looks good."


### 3. Python3
- Version 3.8 or higher because [`SharedMemory`](https://docs.python.org/zh-cn/3/library/multiprocessing.shared_memory.html) is not supported in version 3.7 or lower