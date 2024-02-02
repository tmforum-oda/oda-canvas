package org.tmforum.oda.canvas.portal.component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.configuration.KubernetesProperties;

import io.fabric8.kubernetes.api.model.Namespace;
import io.fabric8.kubernetes.api.model.NamespaceBuilder;


@Service
public class NamespaceService {

    private KubernetesProperties kubernetesProperties;

    public NamespaceService(KubernetesProperties kubernetesProperties) {
        this.kubernetesProperties = kubernetesProperties;
    }

    public NamespaceDto getNamespace() throws IOException {
        String namespace;
        if (System.getenv("KUBERNETES_SERVICE_HOST") != null) {
            namespace = Files.readString(Paths.get("/var/run/secrets/kubernetes.io/serviceaccount/namespace"));
        }
        else {
            namespace = kubernetesProperties.getNamespace();
        }
        NamespaceDto namespaceDto = new NamespaceDto();
        namespaceDto.setNamespace(namespace);
        return namespaceDto;
    }

}
