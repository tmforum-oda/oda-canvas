package org.tmforum.oda.canvas.portal.helm.client;

import lombok.AllArgsConstructor;
import lombok.Builder;

/**
 * helm客户端配置
 *
 * @author li.peilong
 * @date 2022/12/08
 */
@Builder
@AllArgsConstructor
public class HelmClientConfig {
    // kubeConfig文件地址
    private String kubeConfig;
    // if true, the Kubernetes API server's certificate will not be checked for validity. This will make your HTTPS connections insecure
    @Builder.Default
    private Boolean kubeInsecureSkipTlsVerify = Boolean.TRUE;
    // name of the kubeconfig context to use
    private String kubeContext;
    // the address and the port for the Kubernetes API server
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
