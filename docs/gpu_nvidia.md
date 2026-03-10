lsmod | grep nvidia
nvidia-smi -L
nvidia-smi
```
nvidia_uvm           2154496  4
nvidia_drm            135168  5
nvidia_modeset       1814528  3 nvidia_drm
nvidia              14376960  80 nvidia_uvm,nvidia_modeset
drm_ttm_helper         16384  1 nvidia_drm
video                  77824  2 asus_wmi,nvidia_modeset
GPU 0: NVIDIA GeForce RTX 5070 Ti (UUID: GPU-c7fcd789-356f-cd27-6100-90ece2b00da0)
Sat Jan 17 17:18:12 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.95.05              Driver Version: 580.95.05      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 5070 Ti     Off |   00000000:01:00.0 Off |                  N/A |
|  0%   33C    P8             17W /  300W |    3989MiB /  16303MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            1785      G   /usr/lib/xorg/Xorg                        4MiB |
|    0   N/A  N/A            1851      C   ...-mcp-server/.venv/bin/python3       3966MiB |
+-----------------------------------------------------------------------------------------+
```