package org.tmforum.oda.canvas.portal.helm.client.operation;


import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

/**
 * 提供helm信息相关操作
 *
 * @author li.peilong
 * @date 2022/12/08
 */
public class InfoOperation extends BaseOperation {
    private static final String GET_HELM_VERSION_CMD = "helm version";
    private static final String GET_HELM_ENV_CMD = "helm env";

    /**
     * 获取helm的版本信息
     *
     * @return
     * @throws BaseAppException
     */
    public String version() throws BaseAppException {
        return exec(GET_HELM_VERSION_CMD);
    }

    /**
     * 获取helm环境信息
     *
     * @return
     * @throws BaseAppException
     */
    public String env() throws BaseAppException {
        return exec(GET_HELM_ENV_CMD);
    }
}
