package org.tmforum.oda.canvas.portal.helm;

import org.apache.commons.lang3.StringUtils;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientConfig;

import com.google.common.base.Joiner;

@Configuration
@EnableConfigurationProperties(HelmProperties.class)
public class HelmConfiguration {

    @Bean
    public HelmClient helmClient(HelmProperties helmProperties) throws BaseAppException {
        HelmClient.HelmClientBuilder builder = HelmClient.builder();
        HelmClientConfig.HelmClientConfigBuilder helmClientConfigBuilder = HelmClientConfig.builder();
        helmClientConfigBuilder.kubeInsecureSkipTlsVerify(helmProperties.isKubeInsecureSkipTlsVerify());
        if (StringUtils.isNotEmpty(helmProperties.getKubeConfig())) {
            helmClientConfigBuilder.kubeConfig(helmProperties.getKubeConfig());
        }
        if (StringUtils.isNotEmpty(helmProperties.getKubeApiserver())) {
            helmClientConfigBuilder.kubeApiserver(helmProperties.getKubeApiserver());
        }
        builder.helmClientConfig(helmClientConfigBuilder.build());
        HelmClient helmClient = builder.build();
        if (StringUtils.isEmpty(helmProperties.getRepoUrl())) {
            return helmClient;
        }
        // do helm repo add
        helmClient.repos().add(Joiner.on("-").join("tmfoda", helmProperties.getRepoName()),
                helmProperties.getRepoUrl(), helmProperties.getRepoUsername(),
                helmProperties.getRepoPassword(), true);
        return helmClient;
    }

}
