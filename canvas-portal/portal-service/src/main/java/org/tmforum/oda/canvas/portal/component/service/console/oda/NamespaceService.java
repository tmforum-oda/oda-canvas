package org.tmforum.oda.canvas.portal.component.service.console.oda;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.kubernetes.KubernetesProperties;
import org.tmforum.oda.canvas.portal.component.controller.console.dto.Namespace;

@Service
public class NamespaceService {

    @Autowired
    private KubernetesProperties kubernetesProperties;

    public Namespace getNamespace() {
        return new Namespace(kubernetesProperties.getNamespace());
    }
}
