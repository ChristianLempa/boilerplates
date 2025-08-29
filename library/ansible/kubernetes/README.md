# Kubernetes (K8s) Installation Script

- Introduction
- Prerequisites
- Execution Instructions

## Introduction

> The objective of this playbook is to automate the installation and setup of a kubernetes instance. The playbook consist of 3 main plays. For both controller and nodes, for controller only and for nodes only. It will ask user confirmation before moving on to each stage. By the end of the playbook two files will be created on the controller node named **worker_conn_string** and locally inside the playbook directory with the name **Remote_Files/worker_conn_string**. This will have the **connection string**. (Note:- If you want to join controllers or nodes manually later. For controllers use **--control-plane** flag)

### References

**Documentation** - [https://kubernetes.io/docs/setup/](https://kubernetes.io/docs/setup/)

## Prerequisites

- Atleast 2 VMs  (1 For Control Node and 1 For Worker Node).
- Static IPs should be set along with unique host names.
- Inventory should be in this format

```ini
    [controllers]
    host_name ansible_ssh_host=<IP> ansible_user='<USERNAME>' ansible_become_pass='<PASSWORD>'

    [nodes]

    [instance:children]
    controllers
    nodes
```

(If you want to change this, don't forget to change the `inst-k8s` as well)

## Execution Instructions

```bash
ansible-playbook -i <INVENTORY> <PLAYBOOK>
```

### Optional Flags

| Flag  | Use Case |
|-------|-----------|
| --ask-vault-pass | If the vault is encrypted |
| --start-at-task | If you want to start from a specific task|
| --tags | If you want to only run a specific group of tasks|
