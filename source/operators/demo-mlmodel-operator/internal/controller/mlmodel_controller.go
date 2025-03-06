/*
Copyright 2025.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controller

import (
	"context"
	"fmt"
	"github.com/tmforum-oda/oda-canvas/internal/util"
	v5 "k8s.io/api/apps/v1"
	v4 "k8s.io/api/batch/v1"
	v2 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"time"

	odatmforumorgv1beta1 "github.com/tmforum-oda/oda-canvas/api/v1beta1"
)

var (
	logger           = log.Log.WithName("mlmodelController")
	ModelFinalizer   = "mlmodel.finalizer"
	CheckForPVCState = false
	DockerImagePoc   = "ealen/echo-server"
	config           = util.GetConfig()
)

// MLModelReconciler reconciles a MLModel object
type MLModelReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

func (r *MLModelReconciler) pvcName(mlmodel *odatmforumorgv1beta1.MLModel) string {
	return mlmodel.Name + "-pvc"
}

func (r *MLModelReconciler) jobName(mlmodel *odatmforumorgv1beta1.MLModel) string {
	return mlmodel.Name + "-download-job"
}

func (r *MLModelReconciler) deploymentName(mlmodel *odatmforumorgv1beta1.MLModel) string {
	return mlmodel.Name + "-server"
}

func (r *MLModelReconciler) serviceName(mlModel *odatmforumorgv1beta1.MLModel) string {
	return mlModel.Name + "-service"
}

// +kubebuilder:rbac:groups=oda.tmforum.org.oda.tmforum.org,resources=mlmodels,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=oda.tmforum.org.oda.tmforum.org,resources=mlmodels/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=oda.tmforum.org.oda.tmforum.org,resources=mlmodels/finalizers,verbs=update

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the MLModel object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.19.0/pkg/reconcile
func (r *MLModelReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	//log for this context
	_ = log.FromContext(ctx)
	mlModel := &odatmforumorgv1beta1.MLModel{}
	if err := r.Get(ctx, req.NamespacedName, mlModel); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	if !mlModel.ObjectMeta.DeletionTimestamp.IsZero() {
		//this means the reconciliation process is being triggered by a delete event
		return r.deleteResources(ctx, mlModel)
	}

	if needsUpdate(mlModel) {
		logger.Info("Model needs update")
		mlModel.Status.ObservedGeneration = mlModel.Generation
		mlModel.Status.Phase = odatmforumorgv1beta1.StatePending
		return r.updateStatusAndRequeueOrFail(ctx, mlModel)
	}

	if mlModel.Status.Phase == "" {
		//setup initial state
		mlModel.Status.Phase = odatmforumorgv1beta1.StatePending
		return r.updateStatusAndRequeueOrFail(ctx, mlModel)
	} else if mlModel.Status.Phase == odatmforumorgv1beta1.StatePending {
		return r.createPVC(ctx, mlModel)
	} else if mlModel.Status.Phase == odatmforumorgv1beta1.StateCreatingStorage {
		return r.proceedToDownloadingState(ctx, mlModel)
	} else if mlModel.Status.Phase == odatmforumorgv1beta1.StateDownloading {
		return r.proceedToServingState(ctx, mlModel)
	} else if mlModel.Status.Phase == odatmforumorgv1beta1.StateServing {
		return r.proceedToDeployedState(ctx, mlModel)
	}
	return ctrl.Result{}, nil
}

func needsUpdate(mlModel *odatmforumorgv1beta1.MLModel) bool {
	return mlModel.Status.ObservedGeneration != mlModel.Generation &&
		(mlModel.Status.Phase == odatmforumorgv1beta1.StateReady || mlModel.Status.Phase == odatmforumorgv1beta1.StateFailed)
}

func (r *MLModelReconciler) deleteResources(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	logger.Info("MLModel is being deleted, cleaning up resources")

	// Call cleanup function
	if err := r.cleanupResources(ctx, mlModel); err != nil {
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}

	// Remove finalizer and update
	controllerutil.RemoveFinalizer(mlModel, ModelFinalizer)
	if err := r.Update(ctx, mlModel); err != nil {
		return ctrl.Result{}, err
	}
	return ctrl.Result{}, nil
}

func (r *MLModelReconciler) createPVC(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	logger.Info("Model state is pending")

	//check if the pvc already exists
	pvc := &v2.PersistentVolumeClaim{}
	if err := r.Get(ctx, client.ObjectKey{Namespace: mlModel.Namespace, Name: r.pvcName(mlModel)}, pvc); err == nil {
		logger.Info("PVC already exists")
		return ctrl.Result{}, nil
	}

	claim := v2.PersistentVolumeClaim{
		ObjectMeta: ctrl.ObjectMeta{
			Name:      r.pvcName(mlModel),
			Namespace: mlModel.Namespace,
		},
		Spec: v2.PersistentVolumeClaimSpec{
			AccessModes: []v2.PersistentVolumeAccessMode{v2.ReadWriteOnce},
			Resources: v2.VolumeResourceRequirements{
				Requests: v2.ResourceList{
					v2.ResourceStorage: resource.MustParse(mlModel.Spec.StorageSize),
				},
			},
		},
	}

	if err := r.Create(ctx, &claim); err != nil {
		logger.Error(err, "Failed to create PVC")
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}

	logger.Info("PVC created. Now adding finalizer")
	if !controllerutil.ContainsFinalizer(mlModel, ModelFinalizer) {
		controllerutil.AddFinalizer(mlModel, ModelFinalizer)
		if err := r.Update(ctx, mlModel); err != nil {
			return ctrl.Result{}, err
		}
	}

	mlModel.Status.Phase = odatmforumorgv1beta1.StateCreatingStorage
	return r.updateStatusAndRequeueOrFail(ctx, mlModel)
}

func (r *MLModelReconciler) proceedToDownloadingState(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	//check the status of the pvc
	pvcName := r.pvcName(mlModel)

	pvc := &v2.PersistentVolumeClaim{}
	if err := r.Get(ctx, client.ObjectKey{Namespace: mlModel.Namespace, Name: pvcName}, pvc); err != nil {
		logger.Error(err, "Failed to get PVC with name: "+pvcName)
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}

	if config.EnsureStorageAvailability {
		if pvc.Status.Phase != v2.ClaimBound {
			logger.Info("PVC is not bound yet, requesting requeue")
			return ctrl.Result{RequeueAfter: time.Second * 5}, nil
		}
	}

	/*
		checking if existing job is running. Due to K8s sheer amount of speed,
		we might have reached this point after the job was created but before it started running,
		so we have to check for its existence and status here as well
	*/
	var job = v4.Job{}
	if err := r.Get(ctx, client.ObjectKey{Namespace: mlModel.Namespace, Name: r.jobName(mlModel)}, &job); err == nil {
		if job.Status.Succeeded <= 0 {
			logger.Info("Download job is still running")
			return ctrl.Result{RequeueAfter: time.Second * 5}, nil
		}
	}

	//if the pvc is bound, we can start downloading the model
	logger.Info("proceeding to downloading state")
	command := fmt.Sprintf("wget %s -O /mnt/model/tf_model.h5", mlModel.Spec.ModelURL)
	backoffLimit := int32(3)
	ttlSecondsAfterCompletion := int32(120)
	//start downloading the model
	job = v4.Job{
		ObjectMeta: metav1.ObjectMeta{
			Name:      r.jobName(mlModel),
			Namespace: mlModel.Namespace,
			Labels: map[string]string{
				"job-name": r.jobName(mlModel),
			},
		},
		Spec: v4.JobSpec{
			Template: v2.PodTemplateSpec{
				Spec: v2.PodSpec{
					Containers: []v2.Container{
						{
							Name:    mlModel.Name + "-download-container",
							Image:   "busybox",
							Command: []string{"sh", "-c", command},
							VolumeMounts: []v2.VolumeMount{
								{
									Name:      "model-storage",
									MountPath: "/mnt/model",
								},
							},
						},
					},
					Volumes: []v2.Volume{
						{
							Name: "model-storage",
							VolumeSource: v2.VolumeSource{
								PersistentVolumeClaim: &v2.PersistentVolumeClaimVolumeSource{
									ClaimName: r.pvcName(mlModel),
								},
							},
						},
					},
					RestartPolicy: v2.RestartPolicyOnFailure,
				},
			},
			BackoffLimit:            &backoffLimit,
			TTLSecondsAfterFinished: &ttlSecondsAfterCompletion,
		},
	}

	if err := r.Create(ctx, &job); err != nil {
		logger.Error(err, "Failed to create download job. retrying")
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}
	mlModel.Status.Phase = odatmforumorgv1beta1.StateDownloading
	return r.updateStatusAndRequeueOrFail(ctx, mlModel)
}

func (r *MLModelReconciler) proceedToServingState(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	job := &v4.Job{}
	if err := r.Get(ctx, client.ObjectKey{Namespace: mlModel.Namespace, Name: r.jobName(mlModel)}, job); err != nil {
		logger.Error(err, "Failed to get download job with name: "+r.jobName(mlModel))
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}

	if job.Status.Succeeded <= 0 {
		for _, condition := range job.Status.Conditions {
			if condition.Type == v4.JobFailed {
				if condition.Reason == "BackoffLimitExceeded" || condition.Reason == "DeadlineExceeded" {
					logger.Info(fmt.Sprintf("Job %s will not retry: %s", job.Name, condition.Reason))
					mlModel.Status.Phase = odatmforumorgv1beta1.StateFailed
					mlModel.Status.Message = fmt.Sprintf("Job %s failed: %s", job.Name, condition.Reason)
					return r.updateStatusAndRequeueOrFail(ctx, mlModel)
				}
			}
		}

		logger.Info("Download job for model " + mlModel.Name + " is still running")
		return ctrl.Result{RequeueAfter: time.Second * 5}, nil
	} else {
		logger.Info("Download job for model " + mlModel.Name + " has finished")
		mlModel.Status.Phase = odatmforumorgv1beta1.StateServing
		return r.updateStatusAndRequeueOrFail(ctx, mlModel)
	}
}

func (r *MLModelReconciler) proceedToDeployedState(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	logger.Info("Creating Deployment for Inference Server")
	deployment := &v5.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      mlModel.Name + "-server",
			Namespace: mlModel.Namespace,
		},
		Spec: v5.DeploymentSpec{
			Replicas: &mlModel.Spec.Replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{"app": mlModel.Name + "-server"},
			},
			Template: v2.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: map[string]string{"app": mlModel.Name + "-server"},
				},
				Spec: v2.PodSpec{
					Containers: []v2.Container{
						{
							Name:  "inference-server",
							Image: DockerImagePoc, // Modify based on the framework
							Args:  []string{"--model_base_path=/models", "--rest_api_port=8501"},
							Ports: []v2.ContainerPort{
								{ContainerPort: 8501},
							},
							VolumeMounts: []v2.VolumeMount{
								{Name: "model-storage", MountPath: "/models"},
							},
						},
					},
					Volumes: []v2.Volume{
						{Name: "model-storage", VolumeSource: v2.VolumeSource{
							PersistentVolumeClaim: &v2.PersistentVolumeClaimVolumeSource{ClaimName: r.pvcName(mlModel)},
						}},
					},
				},
			},
		},
	}
	if err := r.Create(ctx, deployment); err != nil {
		logger.Error(err, "Failed to create deployment")
		return ctrl.Result{RequeueAfter: time.Second * 5}, err
	}
	mlModel.Status.Phase = odatmforumorgv1beta1.StateReady
	mlModel.Status.ServiceEndpoint = mlModel.Name + "-service." + mlModel.Namespace + ".svc.cluster.local:8501"
	mlModel.Status.Message = "Model is ready. Keep in mind that the service is a POC :) :)"
	return r.updateStatusAndRequeueOrFail(ctx, mlModel)
}

func (r *MLModelReconciler) cleanupResources(ctx context.Context, mlModel *odatmforumorgv1beta1.MLModel) error {

	// Delete Deployment
	deployment := &v5.Deployment{}
	if err := r.Get(ctx, client.ObjectKey{Name: r.deploymentName(mlModel), Namespace: mlModel.Namespace}, deployment); err == nil {
		if err := r.Delete(ctx, deployment); err != nil {
			return err
		}
		logger.Info("Deleted Deployment")
	}

	// Delete Job
	job := &v4.Job{}
	if err := r.Get(ctx, client.ObjectKey{Name: r.jobName(mlModel), Namespace: mlModel.Namespace}, job); err == nil {
		if err := r.Delete(ctx, job); err != nil {
			return err
		}
		logger.Info("Deleted Job")
	}

	//delete all pods created by the job with the same label
	pods := &v2.PodList{}
	if err := r.List(ctx, pods, client.MatchingLabels{"job-name": r.jobName(mlModel)}); err == nil {
		for _, pod := range pods.Items {
			if err := r.Delete(ctx, &pod); err != nil {
				return err
			}
		}
		logger.Info("Deleted Pods of Job")
	}

	// Delete PVC
	pvc := &v2.PersistentVolumeClaim{}
	if err := r.Get(ctx, client.ObjectKey{Name: r.pvcName(mlModel), Namespace: mlModel.Namespace}, pvc); err == nil {
		if err := r.Delete(ctx, pvc); err != nil {
			return err
		}
		logger.Info("Deleted PVC")
	}

	// Delete Service
	service := &v2.Service{}
	if err := r.Get(ctx, client.ObjectKey{Name: mlModel.Name + "-service", Namespace: mlModel.Namespace}, service); err == nil {
		if err := r.Delete(ctx, service); err != nil {
			return err
		}
		logger.Info("Deleted Service")
	}

	return nil
}

func (r *MLModelReconciler) updateStatusAndRequeueOrFail(ctx context.Context, model *odatmforumorgv1beta1.MLModel) (ctrl.Result, error) {
	if err := r.Status().Update(ctx, model); err != nil {
		logger.Error(err, "Failed to update status")
		return ctrl.Result{RequeueAfter: time.Second * 5}, fmt.Errorf("failed to update status: %w", err)
	}
	return ctrl.Result{RequeueAfter: time.Second * time.Duration(config.RequeueIntervalSeconds)}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *MLModelReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&odatmforumorgv1beta1.MLModel{}).
		Complete(r)
}
