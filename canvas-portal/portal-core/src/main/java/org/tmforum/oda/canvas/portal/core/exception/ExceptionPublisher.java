package org.tmforum.oda.canvas.portal.core.exception;

/**
 * Encapsulates the framework's ExceptionHandler to improve usability
 * 1. Solves the problem that error codes can only be of String type
 * 2. Fixes the naming issue with publishBussiness
 * 3. Addresses the lack of a publish method that accepts (errorCode, params...)
 *
 * @author li.peilong
 */
public final class ExceptionPublisher {

    private ExceptionPublisher() {

    }

    /**
     * Throws an exception
     *
     * @param errorCode The error code
     * @param params    Parameters for the error code
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within an error code),
     *                  or {@code null} if none
     */
    public static void publish(Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, null, errorCode, params);
    }

    /**
     * Throws a BaseAppException directly, unifying the exception throwing entry point
     *
     * @param e The exception to be thrown
     * @throws BaseAppException
     */
    public static void publish(BaseAppException e) throws BaseAppException {
        throw e;
    }

    /**
     * Throws an exception
     *
     * @param msg       The error message
     * @param errorCode The error code
     * @param params    Parameters for the error code
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within an error code),
     *                  or {@code null} if none
     */
    public static void publish(String msg, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(msg, null, errorCode, params);
    }

    /**
     * Throws an exception
     *
     * @param t         The original exception
     * @param errorCode The error code
     * @param params    Parameters for the error code
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within an error code),
     *                  or {@code null} if none
     */
    public static void publish(Throwable t, Object errorCode, Object... params) throws BaseAppException {
        ExceptionPublisher.publish(null, t, errorCode, params);
    }

    /**
     * Throws an exception
     *
     * @param msg       The error message
     * @param t         The original exception
     * @param errorCode The error code
     * @param params    Parameters for the error code
     *                  an array of arguments that will be filled in for params within
     *                  the error code (params look like "{0}", "{1,date}", "{2,time}" within an error code),
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
     * Constructs a BaseAppException
     *
     * @param msg       The exception description
     * @param t         The original exception
     * @param errorCode The error code
     * @param params    Parameters for the error code
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
     * Constructs a BaseAppException
     *
     * @param errorCode The error code
     * @param params    Parameters for the error code
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
