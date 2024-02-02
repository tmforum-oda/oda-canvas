package org.tmforum.oda.canvas.portal.infrastructure;

import java.util.List;
import java.util.Optional;

import org.apache.commons.collections.CollectionUtils;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;

import io.fabric8.kubernetes.api.model.HasMetadata;
import io.fabric8.kubernetes.api.model.StatusDetails;


public final class K8sResourceUtils {

    private K8sResourceUtils() {

    }

    public static void validateOnDelete(HasMetadata hasMetadata) throws BaseAppException {

    }

    /**
     * 转换statusDetail对象为Boolean，升级kubernetes-client到6.4.1版本 https://github.com/fabric8io/kubernetes-client/blob/master/doc/MIGRATION-v6.md
     * 参考 https://kubernetes.io/docs/reference/kubernetes-api/common-definitions/status/
     *
     * @param statusDetails statusDetails
     * @return
     */
    public static Boolean convertStatusDetails(List<StatusDetails> statusDetails) {
        if (CollectionUtils.isEmpty(statusDetails)) {
            return Boolean.FALSE;
        }
        Optional<StatusDetails> deleteFailed = statusDetails.stream().filter(statusDetails1 -> statusDetails1.getCauses() != null).findAny();
        if (deleteFailed.isPresent()) {
            return Boolean.FALSE;
        }
        else {
            return Boolean.TRUE;
        }
    }

}
