# Prerequisite

    NVIDIA container toolkit
        sudo apt -y install build-essential nvidia-cuda-toolkit nvidia-headless-495 nvidia-utils-495 libnvidia-encode-495 \
            && distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
            && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
            && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list \
            && sudo apt update \
            && sudo apt -y install nvidia-container-toolkit nvidia-container-runtime nvidia-docker2 

## Deployment

1. Modify the prometheus configuration template  `/etc/prometheus/prometheus.yml` location.
# Job for Nvidia SMI exporter in prometheus config file
        - job_name: 'nvidia_smi_exporter'
          static_configs:
            - targets: ['nvidia_smi_exporter:9835'] # if nvidia_smi_exporter container is not on same docker network , change this line to "- targets: ['whichever ip your host is:9835']"

# Additional Referfences
[Nvidia container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#install-guide)
[Nvidia GPU exporter Documentation](https://github.com/utkuozdemir/nvidia_gpu_exporter)
[Official Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
[Some grafana dashboard, not perfect, old, but configurable](https://grafana.com/grafana/dashboards/14574)