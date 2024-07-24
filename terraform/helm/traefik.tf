resource "kubernetes_namespace" "traefik" {
    
    metadata {
        name = "traefik"
    }

}

resource "helm_release" "traefik" {
    
    depends_on = [kubernetes_namespace.traefik]

    name = "traefik"
    namespace = "traefik"

    repository = "https://helm.traefik.io/traefik"
    chart      = "traefik"

    # Set Traefik as the Default Ingress Controller
    set {
        name  = "ingressClass.enabled"
        value = "true"
    }
    set {
        name  = "ingressClass.isDefaultClass"
        value = "true"
    }
    
    # Default Redirect
    set {
        name  = "ports.web.redirectTo"
        value = "websecure"
    }

    # Enable TLS on Websecure
    set {
        name  = "ports.websecure.tls.enabled"
        value = "true"
    }

    # TLS Options (that's not working for some reason...)
    set {
        name  = "tlsOptions.default.minVersion"
        value = "VersionTLS12"
    }   
}
