package org.tmforum.oda.canvas.portal.helm.client;

import lombok.AllArgsConstructor;
import lombok.Builder;

/**
 * helm client config
 *
 * @author li.peilong
 * @date 2022/12/08
 */
@Builder
@AllArgsConstructor
public class HelmClientConfig {
    /**
     * kubeconfig path
     */
    private String kubeConfig;

    /**
     * if true, the Kubernetes API server's certificate will not be checked for validity. This will make your HTTPS connections insecure
     */
    @Builder.Default
    private Boolean kubeInsecureSkipTlsVerify = Boolean.TRUE;

    private String kubeContext;

    private String kubeApiserver;
    public String getKubeConfig() {
        return kubeConfig;
    }

    public void setKubeConfig(String kubeConfig) {
        this.kubeConfig = kubeConfig;
    }

    public Boolean getKubeInsecureSkipTlsVerify() {
        return kubeInsecureSkipTlsVerify;
    }

    public void setKubeInsecureSkipTlsVerify(Boolean kubeInsecureSkipTlsVerify) {
        this.kubeInsecureSkipTlsVerify = kubeInsecureSkipTlsVerify;
    }

    public String getKubeContext() {
        return kubeContext;
    }

    public void setKubeContext(String kubeContext) {
        this.kubeContext = kubeContext;
    }

    public String getKubeApiserver() {
        return kubeApiserver;
    }

    public void setKubeApiserver(String kubeApiserver) {
        this.kubeApiserver = kubeApiserver;
    }
}
