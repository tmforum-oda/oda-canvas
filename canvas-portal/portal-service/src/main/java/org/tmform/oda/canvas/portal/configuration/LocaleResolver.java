package org.tmform.oda.canvas.portal.configuration;

import java.util.Locale;

import org.apache.commons.lang3.StringUtils;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

public class LocaleResolver implements org.springframework.web.servlet.LocaleResolver  {
    @Override
    public Locale resolveLocale(HttpServletRequest request) {
        String localeFromParameter = request.getParameter("locale");
        Locale locale = resolveLocale(localeFromParameter);
        if (locale != null) {
            return locale;
        }

        String localeFromCookie = findLocaleFromCookie(request, "LOCALE");
        locale = resolveLocale(localeFromCookie);
        if (locale != null) {
            return locale;
        }

        String localeFromHeader = request.getHeader("LOCALE");
        locale = resolveLocale(localeFromHeader);
        if (locale != null) {
            return locale;
        }
        return request.getLocale();
    }

    /**
     * 从字符串中解析出Locale对象
     *
     * @param locale
     * @return
     */
    private Locale resolveLocale(String locale) {
        if (StringUtils.isEmpty(locale)) {
            return null;
        }
        if (locale.indexOf("_") != -1) {
            String[] locales = locale.split("_");
            String language = locales[0];
            String country = locales[1];
            return new Locale(language, country);
        }
        if ("zh".equals(locale)) {
            return Locale.SIMPLIFIED_CHINESE;
        }
        else if ("en".equals(locale)) {
            return Locale.US;
        }
        else {
            return new Locale(locale);
        }
    }

    @Override
    public void setLocale(HttpServletRequest request, HttpServletResponse response, Locale locale) {
    }

    private String findLocaleFromCookie(HttpServletRequest request, String name) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (name.equals(cookie.getName())) {
                    return cookie.getValue();
                }
            }
        }
        return null;
    }
}
