package org.tmforum.oda.canvas.portal.component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.tmforum.oda.canvas.portal.configuration.KubernetesProperties;

import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientException;


@Service
public class NamespaceService {

    private KubernetesProperties kubernetesProperties;

    private KubernetesClient kubernetesClient;

    //private static final Logger LOGGER = LoggerFactory.getLogger(NamespaceService.class);

    public NamespaceService(KubernetesProperties kubernetesProperties, KubernetesClient kubernetesClient) {
        this.kubernetesProperties = kubernetesProperties;
        this.kubernetesClient = kubernetesClient;
    }

    public List<String> getNamespaces() throws IOException {
        if (StringUtils.hasLength(kubernetesProperties.getNamespace())) {
            return Arrays.asList(kubernetesProperties.getNamespace().split(","));
        }
        if (System.getenv("KUBERNETES_SERVICE_HOST") != null) {
            try {
                return kubernetesClient.namespaces().list().getItems().stream().map(ns -> ns.getMetadata().getName()).collect(Collectors.toList());
            }
            catch (KubernetesClientException e) {
                //LOGGER.warn(e);
                return Arrays.asList(Files.readString(Paths.get("/var/run/secrets/kubernetes.io/serviceaccount/namespace")));
            }
        }
        return null;
    }

}
