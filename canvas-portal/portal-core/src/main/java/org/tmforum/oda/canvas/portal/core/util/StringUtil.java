package org.tmforum.oda.canvas.portal.core.util;

import org.apache.commons.lang3.StringUtils;

public class StringUtil {

    private StringUtil() {
    }

    public static String format(String format, Object... args) {
        return StringUtils.isEmpty(format) ? null : String.format(format.replace("%", "%%").replace("{}", "%s"), args);
    }
}
