package org.tmform.oda.canvas.portal.helm;

import org.springframework.boot.context.properties.ConfigurationProperties;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@ConfigurationProperties(prefix = "helm.repo")
@Setter
@Getter
@NoArgsConstructor
public class HelmProperties {

    private String reponame;

    /**
     * repo url
     */
    private String url;

    private String username;


    private String password;

    private boolean insecureSkipTlsVerify;

    private String kubeconfig;

    private boolean kubeInsecureSkipTlsVerify;
}
