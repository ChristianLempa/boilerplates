data civo_loadbalancer "traefik_lb" {

    depends_on = [helm_release.traefik]
  
    name = "k8s_demo_1-traefik-traefik"
}

output "civo_loadbalancer_output" {
    value = data.civo_loadbalancer.traefik_lb.public_ip
}
