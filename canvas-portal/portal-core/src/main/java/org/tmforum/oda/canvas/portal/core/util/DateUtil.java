package org.tmforum.oda.canvas.portal.core.util;

import java.sql.Timestamp;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

import org.apache.commons.lang3.StringUtils;

/**
 * 日期工具类
 *
 * @author henry
 * @version 9.0.2
 * @CreateDate May 24, 2017
 */
public abstract class DateUtil {

    /**
     * 得到SimpleDateFormat实例
     *
     * @param format 格式
     * @return SimpleDateFormat
     * @author henry
     */
    private static SimpleDateFormat getDateFormat(String format) {
        return new SimpleDateFormat(format);
    }

    /**
     * 根据时间字符串，自动匹配格式来格式化成日期
     *
     * @param date 日期
     * @return 日期
     * @author henry
     */
    public static Date formatDateWithAuto(String date) {
        Date ret = null;
        if (date == null || date.length() == 0) {
            return null;
        }
        if (date.length() > 11) {
            if (date.indexOf('-') > 0) {
                if (date.indexOf(':') > 0) {
                    ret = formatDate(date, DateConstants.DATETIME_FORMAT_1);
                }
                else {
                    ret = formatDate(date, DateConstants.DATETIME_FORMAT_3);
                }
            }
            else if (date.indexOf('/') > 0) {
                ret = formatDate(date, DateConstants.DATETIME_FORMAT_4);
            }
            else {
                ret = formatDate(date, DateConstants.DATETIME_FORMAT_2);
            }
        }
        else {
            if (date.indexOf('-') > 0) {
                ret = formatDate(date, DateConstants.DATE_FORMAT_1);
            }
            else if (date.length() == 8) {
                ret = formatDate(date, DateConstants.DATE_FORMAT_2);
            }
            else {
                ret = formatDate(date, DateConstants.DATE_FORMAT_3);
            }
        }
        return ret;
    }

    /**
     * 字符串格式化成日期(带格式)
     *
     * @param date   日期
     * @param format 格式
     * @return 日期
     * @author henry
     */
    public static Date formatDate(String date, String format) {
        if (StringUtils.isEmpty(date)) {
            return null;
        }

        SimpleDateFormat simpleDateFormat = getDateFormat(format);
        try {
            return simpleDateFormat.parse(date);
        }
        catch (ParseException e) {
            throw new IllegalArgumentException("the date string " + date + " is not matching format", e);
        }
    }

    /**
     * 字符串格式化成日期
     *
     * @param date 日期
     * @return 日期
     * @author henry
     */
    public static java.sql.Date formatSQLDate(String date) {
        return formatSQLDateTime(date, DateConstants.DATE_FORMAT);
    }

    /**
     * 字符串格式化成日期(带时分秒)
     *
     * @param date 日期
     * @return 日期
     * @author henry
     */
    public static java.sql.Date formatSQLDateTime(String date) {
        return formatSQLDateTime(date, DateConstants.DATE_FORMAT_TIME);
    }

    /**
     * 字符串格式化成日期(带格式)
     *
     * @param date   日期
     * @param format 格式
     * @return 日期
     * @author henry
     */
    public static java.sql.Date formatSQLDateTime(String date, String format) {
        if (StringUtils.isEmpty(date)) {
            return null;
        }

        SimpleDateFormat simpleDateFormat = getDateFormat(format);
        try {
            Date tmpDate = simpleDateFormat.parse(date);
            Timestamp time = new Timestamp(tmpDate.getTime());
            return new java.sql.Date(time.getTime());
        }
        catch (ParseException e) {
            throw new IllegalArgumentException(
                    "the date string " + date + " is not matching format " , e);
        }
    }

    /**
     * 日期转换成字符串(带格式)
     *
     * @param date   日期
     * @param format 格式
     * @return 日期
     * @author henry
     */
    public static String formatString(Date date, String format) {
        if (date == null) {
            return null;
        }
        SimpleDateFormat sdf = getDateFormat(format);
        return sdf.format(date);
    }

    /**
     * 日期转换成字符串
     *
     * @param date 日期
     * @return 日期
     * @author henry
     */
    @Deprecated
    public static String formatString(java.sql.Date date) {
        return formatString(date, DateConstants.DATE_FORMAT);
    }

    /**
     * 日期转换成字符串(带时分秒)
     *
     * @param date 日期
     * @return 日期
     * @author henry
     */
    @Deprecated
    public static String formatTimeString(java.sql.Date date) {
        return formatString(date, DateConstants.DATE_FORMAT_TIME);
    }

    /**
     * 日期转换成字符串(带格式)
     *
     * @param date   日期
     * @param format 格式
     * @return 日期
     * @author henry
     */
    @Deprecated
    public static String formatString(java.sql.Date date, String format) {
        if (date == null) {
            return null;
        }
        SimpleDateFormat sdf = getDateFormat(format);
        return sdf.format(date);
    }

    /**
     * 日期之间的比较，如果其中一个日期为NULL，就表示日期最大值
     *
     * @param beginDate 开始日期
     * @param endDate   结束日期
     * @return int
     * @author henry
     */
    public static int compare(Date beginDate, Date endDate) {
        int ret = DateConstants.EQ;
        if (beginDate != null && endDate == null) {
            ret = DateConstants.LT;
        }
        else if (beginDate == null && endDate != null) {
            ret = DateConstants.GT;
        }
        else if (beginDate != null && endDate != null) {
            long beginTime = beginDate.getTime();
            long endTime = endDate.getTime();

            if (beginTime > endTime) {
                ret = DateConstants.GT;
            }
            else if (beginTime == endTime) {
                ret = DateConstants.EQ;
            }
            else if (beginTime < endTime) {
                ret = DateConstants.LT;
            }
        }
        return ret;
    }

    /**
     * 日期常量池值
     *
     * @author henry
     * @version 9.0.2
     * @CreateDate Jun 13, 2017
     */
    public abstract static class DateConstants {
        /**
         * Number of milliseconds in a standard second.
         */
        public static final long MILLIS_PER_SECOND = 1000;

        /**
         * Number of milliseconds in a standard minute.
         */
        public static final long MILLIS_PER_MINUTE = 60 * MILLIS_PER_SECOND;

        /**
         * Number of milliseconds in a standard hour.
         */
        public static final long MILLIS_PER_HOUR = 60 * MILLIS_PER_MINUTE;

        /**
         * Number of milliseconds in a standard day.
         */
        public static final long MILLIS_PER_DAY = 24 * MILLIS_PER_HOUR;

        /**
         * Number of milliseconds in a standard week.
         */
        public static final long MILLIS_PER_WEEK = 7 * MILLIS_PER_DAY;

        /**
         * 秒
         */
        public static final int SECOND = 0;

        /**
         * 分
         */
        public static final int MINUTE = 1;

        /**
         * 时
         */
        public static final int HOUR = 2;

        /**
         * 天
         */
        public static final int DAY = 3;

        /**
         * 日期格式
         */
        public static final String DATE_FORMAT = "yyyy-MM-dd";

        /**
         * 日期时分秒格式
         */
        public static final String DATE_FORMAT_TIME = "yyyy-MM-dd HH:mm:ss";

        /**
         * 大于(&gt;)
         */
        public static final int GT = 2;

        /**
         * 小于(&lt;)
         */
        public static final int LT = 0;

        /**
         * 等于
         */
        public static final int EQ = 1;


        /**
         * 日期格式1
         */
        public static final String DATE_FORMAT_1 = DATE_FORMAT; //"yyyy-MM-dd";

        /**
         * 日期格式2
         */
        public static final String DATE_FORMAT_2 = "yyyyMMdd";

        /**
         * 日期格式3
         */
        public static final String DATE_FORMAT_3 = "yyyy年MM月dd日";

        /**
         * 日期时分秒格式1
         */
        public static final String DATETIME_FORMAT_1 = DATE_FORMAT_TIME; //"yyyy-MM-dd HH:mm:ss";

        /**
         * 日期时分秒格式2
         */
        public static final String DATETIME_FORMAT_2 = "yyyyMMddHHmmss";

        /**
         * 日期时分秒格式3
         */
        public static final String DATETIME_FORMAT_3 = "yyyy-MM-dd HH-mm-ss";


        /**
         * 日期时分秒格式4
         */
        public static final String DATETIME_FORMAT_4 = "yyyy/MM/dd HH:mm:ss";
    }
}
