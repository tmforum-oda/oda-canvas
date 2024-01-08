package org.tmforum.oda.canvas.portal.core.exception;

/**
 * 定义异常错误码
 * Created by li.peilong on 2017/5/20.
 */
public enum CoreExceptionErrorCode implements ExceptionErrorCode {

    //utils(00100~00149)
    UNKNOWN("CORE-00000"),
    FAILED_PARSE_JSON_PATH("CORE-00100"),
    FAILED_PARSE_JSON_PATH_TO_TYPE("CORE-00101");

    private String code;

    CoreExceptionErrorCode(String code) {
        this.code = code;
    }

    @Override
    public String toString() {
        return this.code;
    }
}
