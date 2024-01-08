package org.tmforum.oda.canvas.portal.core.exception;


/**
 * 对框架ExceptionHandler进行封装，提高易用性
 * 1.解决错误码只能是String类型问题
 * 2.解决publishBussiness名称问题
 * 3.解决无publish(errorCode,param...)问题
 * Created by li.peilong on 2017/5/20.
 */
public final class ExceptionPublisher {

    private ExceptionPublisher() {

    }

    /**
     * 抛出异常
     *
     * @param errorCode 错误码
     * @param params    错误码参数
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within a error code),
     *                  or {@code null} if none
     */
    public static void publish(Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, null, errorCode, params);
    }

    /**
     * 将BaseAppException异常直接抛出，统一异常抛出入口
     *
     * @param e
     * @throws BaseAppException
     */
    public static void publish(BaseAppException e) throws BaseAppException {
        throw e;
    }

    /**
     * 抛出异常
     *
     * @param msg       错误信息
     * @param errorCode 错误码
     * @param params    错误码参数
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within a error code),
     *                  or {@code null} if none
     */
    public static void publish(String msg, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(msg, null, errorCode, params);
    }

    /**
     * 抛出异常
     *
     * @param t         原始异常
     * @param errorCode 错误码
     * @param params    错误码参数
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within a error code),
     *                  or {@code null} if none
     */
    public static void publish(Throwable t, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, t, errorCode, params);
    }

    /**
     * 抛出异常
     *
     * @param msg       错误信息
     * @param t         原始异常
     * @param errorCode 错误码
     * @param params    错误码参数
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within a error code),
     *                  or {@code null} if none
     */
    public static void publish(String msg, Throwable t, Object errorCode, Object... params) throws BaseAppException {
        BaseAppException baseAppException = new BaseAppException();
        baseAppException.setCode((errorCode.toString()));
        String errorMessage = I18nUtils.getMessage(errorCode.toString(), params);
        baseAppException.setMessage(errorMessage == null ? msg : errorMessage);
        throw baseAppException;
    }

    /**
     * 构造一个BaseAppException异常
     *
     * @param msg       异常描述
     * @param t         原始异常
     * @param errorCode 错误码
     * @param params    错误码参数
     * @return
     */
    public static BaseAppException build(String msg, Throwable t, Object errorCode, Object... params) {
        try {
            ExceptionPublisher.publish(msg, t, errorCode, params);
        }
        catch (BaseAppException e) {
            return e;
        }
        return null;
    }

    /**
     * 构造一个BaseAppException异常
     *
     * @param errorCode 错误码
     * @param params    错误码参数
     * @return
     */
    public static BaseAppException build(Object errorCode, Object... params) {
        return build(null, null, errorCode, params);
    }

    private static String convert(Object errorCode) {
        if (errorCode instanceof String) {
            return (String) errorCode;
        }
        return errorCode == null ? null : errorCode.toString();
    }
}
