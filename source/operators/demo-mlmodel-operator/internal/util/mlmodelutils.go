package util

import (
	"github.com/tmforum-oda/oda-canvas/api/v1beta1"
	comvodafonecellv1beta1 "github.com/tmforum-oda/oda-canvas/api/v1beta1"
)

// NeedsUpdate
// Returns true if the MLModel needs to be updated
// The MLModel needs to be updated if the observedGeneration is less than the generation
// and the phase is either Failed or Ready
// /**
func NeedsUpdate(mlModel *v1beta1.MLModel) bool {
	return mlModel.Status.ObservedGeneration < mlModel.Generation &&
		(mlModel.Status.Phase == comvodafonecellv1beta1.StateFailed || mlModel.Status.Phase == comvodafonecellv1beta1.StateReady)
}

func SetModelInitialState(mlModel *v1beta1.MLModel) {
	mlModel.Status.Phase = comvodafonecellv1beta1.StatePending
	mlModel.Status.Message = ""
	mlModel.Status.ServiceEndpoint = ""
	mlModel.Status.ObservedGeneration = mlModel.Generation
}
