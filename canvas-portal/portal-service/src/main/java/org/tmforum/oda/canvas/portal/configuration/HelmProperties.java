package org.tmforum.oda.canvas.portal.configuration;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@ConfigurationProperties(prefix = "helm")
@Setter
@Getter
@NoArgsConstructor
public class HelmProperties {

    private String repoName;

    /**
     * repo url
     */
    private String repoUrl;

    private String repoUsername;


    private String repoPassword;

    private boolean insecureSkipTlsVerify;

    private String kubeConfig;

    private boolean kubeInsecureSkipTlsVerify;

    private String kubeApiserver;
}
