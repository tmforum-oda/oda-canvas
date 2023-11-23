package org.tmform.oda.canvas.portal.kubernetes;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@ConfigurationProperties(prefix = "kubernetes")

@Setter
@Getter
@NoArgsConstructor
public class KubernetesProperties {
    private String masterUrl;

    private String kubeconfig;

    private String namespace;

}
