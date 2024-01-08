package org.tmforum.oda.canvas.portal.helm.client;


import org.tmforum.oda.canvas.portal.core.exception.ExceptionErrorCode;

/**
 * 定义helm client的异常错误码
 *
 * @author li.peilong
 * @date 2022/12/06
 */
public enum HelmClientExceptionErrorCode implements ExceptionErrorCode {
    EXEC_OPERATION_FAILED("HELM-00001"),
    EXEC_OPERATION_TIMEOUT("HELM-00002"),
    WRITE_TMP_FILE_FAILED("HELM-00003"),
    HELM_RELEASE_NOT_EXIST("HELM-00004"),
    HELM_CREATE_DIRECTORY_FAILED("HELM-00005"),
    HELM_UNCOMPRESS_FAILED("HELM-00006"),
    HELM_GET_CHART_STRUCTURE_FAILED("HELM-00007"),
    HELM_GET_CHART_FILE_FAILED("HELM-00008"),
    HELM_SEARCH_CHART_FILE_FAILED("HELM-00009"),
    HELM_CHART_NOT_EXIST("HELM-00010"),

    READ_SERVICE_ACCOUNT_TOKEN_FILE_FAILED("HELM-00011");
    private String code;

    HelmClientExceptionErrorCode(String code) {
        this.code = code;
    }

    @Override
    public String toString() {
        return code;
    }
}
