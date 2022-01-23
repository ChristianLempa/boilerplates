FROM jupyterhub/jupyterhub:0.9.3

COPY jupyterhub_config.py .

RUN wget https://raw.githubusercontent.com/jupyterhub/jupyterhub/0.9.3/examples/cull-idle/cull_idle_servers.py

RUN pip install \
    dockerspawner==0.10.0 \
    jhub_cas_authenticator==1.0.0