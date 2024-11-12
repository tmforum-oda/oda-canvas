kubectl get ingress   -o=custom-columns=NAME:metadata.name,URL:status.loadBalancer.ingress[*].ip
