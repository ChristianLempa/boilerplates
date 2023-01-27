# Prerequisite

    NVIDIA container toolkit
        sudo apt -y install build-essential nvidia-cuda-toolkit nvidia-headless-495 nvidia-utils-495 libnvidia-encode-495 \
            && distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
            && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
            && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list \
            && sudo apt update \
            && sudo apt -y install nvidia-container-toolkit nvidia-container-runtime nvidia-docker2 


    DCGM on host machine running Nvidia GPU 
        wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin \
            && sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600 \
            && sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub \
            && sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /" \
            && sudo apt update \
            && sudo apt install -y datacenter-gpu-manager \
            && sudo systemctl --now enable nvidia-dcgm

## Deployment

1. Modify the prometheus configuration template  `/etc/prometheus/prometheus.yml` location.
# Job for Nvidia DCGM exporter in prometheus config file
        - job_name: 'nvidia_exporter'
          static_configs:
            - targets: ['nvidia_exporter:9400'] # if nvidia_exporter container is not on same docker network , change this line to "- targets: ['whichever ip your host is:9400']"

# Additional Referfences
[Official DCGM Documentations](https://github.com/NVIDIA/DCGM)
[Nvidia container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#install-guide)
[Nvidia DCGM exporter Documentation](https://github.com/NVIDIA/dcgm-exporter)
[Nvidia DCGM exporter Documentation-2](https://docs.nvidia.com/datacenter/cloud-native/gpu-telemetry/dcgm-exporter.html)
[Official Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
[Some grafana dashboard, not perfect, old, but configurable](https://grafana.com/grafana/dashboards/11578)