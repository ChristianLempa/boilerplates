# Kubernetes Cert-Manager Installation Guide

Here is the installation guide for Cert-Manager and the complete configuration.

## Deployment

### 1. Add the Helm Repository & Update

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
```

### 2. Install Cert-Manager with Helm & CRDs

```bash
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

## Configuration

Add your Issuer or ClusterIssuer Objects, Credentails and Certificates.

_For more info visit:_ [Official Cert-Manager Documentation](https://cert-manager.io/docs/)

## Best-Practices & Post-Installation

## Troubleshooting

You can troubleshoot issues and inspect log entries for the Certificate Objects with the `kubectl describe` command.

_For more info visit:_ [Official Cert-Manager Troubleshooting Guide](https://cert-manager.io/docs/faq/troubleshooting/)
