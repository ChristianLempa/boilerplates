

helm repo add jetstack https://charts.jetstack.io


Install CRDs
(option 1) manually:
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.7.0/cert-manager.crds.yaml

Or
install with helm
--set installCRDs=true

$ helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.7.0 \
  # --set installCRDs=true