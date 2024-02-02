package org.tmforum.oda.canvas.portal.helm;

import java.util.List;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.HelmRepo;

/**
 * Provides services related to Helm Repositories
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@Service
public class HelmRepoService {

    private final HelmClient helmClient;

    public HelmRepoService(HelmClient helmClient) {
        this.helmClient = helmClient;
    }

    /**
     * Update
     *
     * @param repos the names of repositories to update
     * @return
     * @throws BaseAppException
     */
    public void update(String... repos) throws BaseAppException {
        helmClient.repos().update(repos);
    }

    /**
     * Get a list of repositories for a tenant
     *
     * @param keyword
     * @return
     * @throws BaseAppException
     */
    public List<HelmRepo> listRepos(String keyword) throws BaseAppException {
        List<HelmRepo> repos = helmClient.repos().list(keyword);
        if (StringUtils.isBlank(keyword)) {
            return repos;
        }
        return repos.stream().filter(helmRepo -> StringUtils.contains(helmRepo.getName(), keyword)).collect(Collectors.toList());
    }
}
