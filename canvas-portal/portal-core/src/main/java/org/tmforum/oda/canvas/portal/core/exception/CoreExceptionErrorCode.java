package org.tmforum.oda.canvas.portal.core.exception;

/**
 * Exception error code
 *
 * @author li.peilong
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
