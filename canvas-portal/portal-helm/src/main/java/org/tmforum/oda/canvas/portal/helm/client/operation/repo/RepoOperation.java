package org.tmforum.oda.canvas.portal.helm.client.operation.repo;

import com.google.common.base.Joiner;
import com.google.common.base.Preconditions;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.util.JsonUtil;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;
import org.tmforum.oda.canvas.portal.helm.client.operation.BaseOperation;
import org.apache.commons.lang3.StringUtils;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * @author liu.jiang
 * @date 2022/11/23 16:23
 */
public class RepoOperation extends BaseOperation {
    private static final String LIST_REPO_CMD = "helm repo list -o json";
    private static final String UPDATE_REPO_CMD = "helm repo update {}";
    private static final String REMOVE_REPO_CMD = "helm repo remove {}";
    private static final String ADD_REPO_CMD = "helm repo add {} {}  --insecure-skip-tls-verify";

    /**
     * 获取仓库列表
     *
     * @param keywords 仓库的名称
     * @return
     */
    public List<HelmRepo> list(String... keywords) throws BaseAppException {
        String output = exec(LIST_REPO_CMD);
        List<HelmRepo> result = JsonUtil.json2List(output, HelmRepo.class);
        if (keywords == null || keywords.length == 0) {
            return result;
        }
        return result.stream()
                .filter(helmRepo -> Stream.of(keywords).anyMatch(keyword -> helmRepo.getName().contains(keyword)))
                .collect(Collectors.toList());
    }

    /**
     *
     * @param name 仓库名
     * @param url 仓库地址
     * @throws BaseAppException
     */
    public void add(String name, String url) throws BaseAppException {
        add(name, url, null, null);
    }

    /**
     * 添加Chart仓库
     *
     * @param name 仓库名
     * @param url 仓库地址
     * @param username 仓库用户名
     * @param password 仓库密码
     * @throws BaseAppException
     */
    public void add(String name, String url, String username, String password) throws BaseAppException {
        add(name, url, username, password, false);
    }

    /**
     * 添加Chart仓库
     *
     * @param name 仓库名
     * @param url 仓库地址
     * @param username 仓库用户名
     * @param password 仓库密码
     * @param overwrite 如果仓库已经添加过，是否重新添加
     * @throws BaseAppException
     */
    public void add(String name, String url, String username, String password, boolean overwrite) throws BaseAppException {
        Preconditions.checkArgument(StringUtils.isNoneBlank(name), "repo name can not be null or empty");
        Preconditions.checkArgument(StringUtils.isNoneBlank(name), "repo url can not be null or empty");
        String cmd = StringUtil.format(ADD_REPO_CMD, name, url);
        if (StringUtils.isNoneBlank(username)) {
            cmd = cmd.concat(" --username=").concat(username);
        }

        if (StringUtils.isNoneBlank(password)) {
            cmd = cmd.concat(" --password=").concat(password);
        }
        if (overwrite) {
            cmd = cmd.concat(" --force-update");
        }
        exec(cmd);
    }

    /**
     * 移除仓库
     * @param repos
     */
    public void remove(String... repos) throws BaseAppException {
        if (repos == null || repos.length == 0) {
            return;
        }
        String cmd = StringUtil.format(REMOVE_REPO_CMD, Joiner.on(" ").join(repos));
        exec(cmd);
    }

    /**
     * 更新仓库
     *
     * @param repos
     */
    public void update(String... repos) throws BaseAppException {
        String repo = "";
        if (repos != null && repos.length > 0) {
            repo = Joiner.on(" ").skipNulls().join(repos);
        }
        String cmd = StringUtil.format(UPDATE_REPO_CMD, repo);
        exec(cmd);
    }

}
