resource "kubernetes_secret" "cloudflare_api_key_secret" {
  
    depends_on = [kubernetes_namespace.your-namespace-object]
    
    metadata {
        name = "cloudflare-api-key-secret"
        namespace = "your-namespace"
    }

    data = {
        api-key = var.your-api-key-variable
    }

    type = "Opaque"
}