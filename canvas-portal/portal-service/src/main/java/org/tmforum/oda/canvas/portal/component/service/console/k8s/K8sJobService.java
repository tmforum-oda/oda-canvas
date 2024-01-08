package org.tmforum.oda.canvas.portal.component.service.console.k8s;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.tmforum.oda.canvas.portal.component.infrastructure.CanvasErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import io.fabric8.kubernetes.api.model.batch.v1.Job;
import io.fabric8.kubernetes.client.KubernetesClient;

/**
 * 提供Kubernetes Job资源相关服务
 *
 * @author li.peilong
 * @date 2022/11/30
 */
@Service
public class K8sJobService {

    @Autowired
    private KubernetesClient kubeClient;

    public Job getJob(String namespace, String name) throws BaseAppException {
        Job job = null;
        try {
            job = kubeClient.batch().v1().jobs().inNamespace(namespace).withName(name).get();
        }
        catch (Exception e) {
            ExceptionPublisher.publish(e, CanvasErrorCode.GET_JOB_FAILED, name, namespace);
        }

        if (job == null) {
            ExceptionPublisher.publish(CanvasErrorCode.JOB_NOT_EXIST, name, namespace);
        }
        return job;
    }
}
