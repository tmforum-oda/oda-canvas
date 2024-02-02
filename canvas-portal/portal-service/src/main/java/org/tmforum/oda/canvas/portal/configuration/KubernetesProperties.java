package org.tmforum.oda.canvas.portal.configuration;

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

    /**
     * absolute path kubeconfig file
     */
    private String kubeconfig;

    private String namespace;

}
