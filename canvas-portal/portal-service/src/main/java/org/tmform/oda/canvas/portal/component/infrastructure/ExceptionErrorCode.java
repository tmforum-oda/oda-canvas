package org.tmform.oda.canvas.portal.component.infrastructure;

/**
 * 操作枚举类
 */
public enum ExceptionErrorCode implements org.tmforum.oda.canvas.portal.core.exception.ExceptionErrorCode {

    // ODA (20121~20140)
    ODA_LIST_COMPONENT_INSTANCE_FAILED("ODA-CANVAS-20121"),
    ODA_GET_COMPONENT_INSTANCE_FAILED("ODA-CANVAS-20122"),
    ODA_COMPONENT_INSTANCE_NOT_EXIST("ODA-CANVAS-20123"),
    ODA_LIST_COMPONENT_API_FAILED("ODA-CANVAS-20124"),
    ODA_GET_COMPONENT_API_FAILED("ODA-CANVAS-20125"),
    ODA_COMPONENT_API_NOT_EXIST("ODA-CANVAS-20126"),
    ODA_LIST_COMPONENT_INSTANCE_EVENTS_FAILED("ODA-CANVAS-20127"),
    ODA_ADD_COMPONENT_FAILED("ODA-CANVAS-20128"),
    ODA_LIST_ORCHESTRATION_FAILED("ODA-CANVAS-20129"),
    ODA_GET_ORCHESTRATION_FAILED("ODA-CANVAS-20130"),
    ODA_ORCHESTRATION_NOT_EXIST("ODA-CANVAS-20131"),
    LIST_ODA_ORCHESTRATION_EVENTS_FAILED("ODA-CANVAS-20132"),
    ODA_CREATE_ORCHESTRATION_FAILED("ODA-CANVAS-20133"),
    ODA_UPDATE_ORCHESTRATION_FAILED("ODA-CANVAS-20134"),
    ODA_COMPONENT_COMPLIACNE_POD_NOT_EXIST("ODA-CANVAS-20135"),
    ODA_COMPONENT_COMPLIACNE_POD_NOT_READY("ODA-CANVAS-20136"),
    ODA_COMPONENT_NOT_EXIST("ODA-CANVAS-20137"),
    ODA_UNSUPPORTED("ODA-CANVAS-20138");

    private final String code;

    /**
     * construtor
     *
     * @param code 错误码
     */
    ExceptionErrorCode(String code) {
        this.code = code;
    }

    /**
     * 获取错误码
     *
     * @return code
     */
    public String code() {
        return code;
    }

    @Override
    public String toString() {
        return this.code;
    }

}
