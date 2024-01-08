package org.tmforum.oda.canvas.portal.component.service.console.helm;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.helm.client.HelmClient;
import org.tmforum.oda.canvas.portal.helm.client.operation.repo.HelmRepo;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 提供Helm Repo相关服务
 *
 * @author li.peilong
 * @date 2023/02/13
 */
@Service
public class HelmRepoService {
    @Autowired
    private HelmClient helmClient;

    /**
     * 更新
     *
     * @param repos 仓库名
     * @return
     * @throws BaseAppException
     */
    public void update(String... repos) throws BaseAppException {
        helmClient.repos().update(repos);
    }

    /**
     * 获取某租户下的仓库列表
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
