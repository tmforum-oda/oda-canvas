package org.tmforum.oda.canvas.portal.core.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.MessageSource;
import org.springframework.context.NoSuchMessageException;
import org.springframework.context.i18n.LocaleContextHolder;

import org.tmforum.oda.canvas.portal.core.util.SpringContext;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;


public abstract class I18nUtils {
    private static Logger logger = LoggerFactory.getLogger(I18nUtils.class);
    private static MessageSource messageSource;

    public static String getMessage(String errorCode, Object[] args) {
        String localeMessage = "";
        try {
            if (messageSource == null) {
                messageSource = SpringContext.getBean(MessageSource.class);
            }
            localeMessage = messageSource.getMessage(errorCode, args, LocaleContextHolder.getLocale());
        }
        catch (NoSuchMessageException e) {
            logger.error("No code named " + errorCode + " found in I18n file");
        }
        catch (IllegalArgumentException e) {
            logger.error(StringUtil.format("Message[{}] argument parse fail", errorCode));
        }
        catch (Exception e) {
            logger.error(StringUtil.format("[{}]Failed to get the internationalization", errorCode));
        }
        return localeMessage;
    }
}