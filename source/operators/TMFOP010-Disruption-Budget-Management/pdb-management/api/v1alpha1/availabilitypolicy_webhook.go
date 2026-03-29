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

package v1alpha1

import (
	"context"
	"fmt"
	"time"

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/util/validation/field"
	ctrl "sigs.k8s.io/controller-runtime"
	logf "sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"
)

// log is for logging in this package.
var availabilitypolicylog = logf.Log.WithName("availabilitypolicy-resource")

// SetupWebhookWithManager sets up the webhook with the Manager.
func (r *AvailabilityPolicy) SetupWebhookWithManager(mgr ctrl.Manager) error {
	return ctrl.NewWebhookManagedBy(mgr).
		For(r).
		WithDefaulter(&AvailabilityPolicyCustomDefaulter{}).
		WithValidator(&AvailabilityPolicyCustomValidator{}).
		Complete()
}

// AvailabilityPolicyCustomDefaulter implements the CustomDefaulter interface
type AvailabilityPolicyCustomDefaulter struct{}

var _ admission.CustomDefaulter = &AvailabilityPolicyCustomDefaulter{}

// Default implements the CustomDefaulter interface
func (d *AvailabilityPolicyCustomDefaulter) Default(ctx context.Context, obj runtime.Object) error {
	r, ok := obj.(*AvailabilityPolicy)
	if !ok {
		return fmt.Errorf("expected an AvailabilityPolicy object but got %T", obj)
	}

	availabilitypolicylog.Info("default", "name", r.Name)

	// Set default priority if not specified
	if r.Spec.Priority == 0 {
		r.Spec.Priority = 50
	}

	// Set default enforcement if not specified
	if r.Spec.Enforcement == "" {
		r.Spec.Enforcement = EnforcementAdvisory
	}

	// Set default timezone for maintenance windows
	for i := range r.Spec.MaintenanceWindows {
		if r.Spec.MaintenanceWindows[i].Timezone == "" {
			r.Spec.MaintenanceWindows[i].Timezone = "UTC"
		}

		// Set default days of week (all days) if not specified
		if len(r.Spec.MaintenanceWindows[i].DaysOfWeek) == 0 {
			r.Spec.MaintenanceWindows[i].DaysOfWeek = []int{0, 1, 2, 3, 4, 5, 6}
		}
	}

	// Set default enforcement if not specified
	if r.Spec.EnforceMinReplicas == nil {
		enforce := true
		r.Spec.EnforceMinReplicas = &enforce
	}

	// Set default for AllowOverride based on enforcement mode
	if r.Spec.AllowOverride == nil {
		allowOverride := true
		if r.Spec.Enforcement == EnforcementStrict {
			allowOverride = false
		}
		r.Spec.AllowOverride = &allowOverride
	}

	// Set default for OverrideRequiresReason
	if r.Spec.OverrideRequiresReason == nil {
		requiresReason := false
		r.Spec.OverrideRequiresReason = &requiresReason
	}

	// For custom class, ensure we have valid defaults
	if r.Spec.AvailabilityClass == Custom && r.Spec.CustomPDBConfig != nil {
		// Default to IfHealthyBudget if not specified
		if r.Spec.CustomPDBConfig.UnhealthyPodEvictionPolicy == "" {
			r.Spec.CustomPDBConfig.UnhealthyPodEvictionPolicy = "IfHealthyBudget"
		}
	}

	// Set MinimumClass default for flexible enforcement
	if r.Spec.Enforcement == EnforcementFlexible && r.Spec.MinimumClass == "" {
		r.Spec.MinimumClass = r.Spec.AvailabilityClass
	}

	return nil
}

// AvailabilityPolicyCustomValidator implements the CustomValidator interface
type AvailabilityPolicyCustomValidator struct{}

var _ admission.CustomValidator = &AvailabilityPolicyCustomValidator{}

// ValidateCreate implements the CustomValidator interface
func (v *AvailabilityPolicyCustomValidator) ValidateCreate(ctx context.Context, obj runtime.Object) (admission.Warnings, error) {
	r, ok := obj.(*AvailabilityPolicy)
	if !ok {
		return nil, fmt.Errorf("expected an AvailabilityPolicy object but got %T", obj)
	}

	availabilitypolicylog.Info("validate create", "name", r.Name)

	var allErrs field.ErrorList
	var warnings admission.Warnings

	// Validate availability class
	if err := validateAvailabilityClass(r); err != nil {
		allErrs = append(allErrs, err)
	}

	// Validate component selector
	if err := validateComponentSelector(r); err != nil {
		allErrs = append(allErrs, err)
	}

	// Validate maintenance windows
	for i, window := range r.Spec.MaintenanceWindows {
		if errs := validateMaintenanceWindow(window, field.NewPath("spec", "maintenanceWindows").Index(i)); len(errs) > 0 {
			allErrs = append(allErrs, errs...)
		}
	}

	// Validate priority
	if r.Spec.Priority < 0 || r.Spec.Priority > 1000 {
		allErrs = append(allErrs, field.Invalid(
			field.NewPath("spec", "priority"),
			r.Spec.Priority,
			"priority must be between 0 and 1000",
		))
	}

	// Validate enforcement configuration
	if errs := validateEnforcementConfiguration(r); len(errs) > 0 {
		allErrs = append(allErrs, errs...)
	}

	// Add warnings for best practices
	if r.Spec.Priority == 0 {
		warnings = append(warnings, "Priority is set to 0, which is the lowest priority. Consider setting a higher value if this policy should take precedence.")
	}

	if len(r.Spec.ComponentSelector.Namespaces) == 0 {
		warnings = append(warnings, "No namespace selector specified. This policy will apply to all namespaces.")
	}

	if r.Spec.Enforcement == EnforcementStrict && r.Spec.AllowOverride != nil && *r.Spec.AllowOverride {
		warnings = append(warnings, "AllowOverride is true but Enforcement is strict. The strict enforcement will ignore this setting.")
	}

	if r.Spec.Enforcement == EnforcementFlexible && r.Spec.MinimumClass == "" {
		warnings = append(warnings, "Flexible enforcement without MinimumClass specified. Will default to the policy's availability class.")
	}

	if len(allErrs) == 0 {
		return warnings, nil
	}

	return warnings, allErrs.ToAggregate()
}

// ValidateUpdate implements the CustomValidator interface
func (v *AvailabilityPolicyCustomValidator) ValidateUpdate(ctx context.Context, oldObj, newObj runtime.Object) (admission.Warnings, error) {
	newPolicy, ok := newObj.(*AvailabilityPolicy)
	if !ok {
		return nil, fmt.Errorf("expected an AvailabilityPolicy object but got %T", newObj)
	}

	oldPolicy, ok := oldObj.(*AvailabilityPolicy)
	if !ok {
		return nil, fmt.Errorf("expected an AvailabilityPolicy object for old object but got %T", oldObj)
	}

	availabilitypolicylog.Info("validate update", "name", newPolicy.Name)

	var warnings admission.Warnings

	// Warn if changing availability class
	if oldPolicy.Spec.AvailabilityClass != newPolicy.Spec.AvailabilityClass {
		warnings = append(warnings, fmt.Sprintf(
			"Changing availability class from %s to %s will affect all matching deployments",
			oldPolicy.Spec.AvailabilityClass, newPolicy.Spec.AvailabilityClass,
		))
	}

	// Warn if changing enforcement mode
	if oldPolicy.Spec.Enforcement != newPolicy.Spec.Enforcement {
		warnings = append(warnings, fmt.Sprintf(
			"Changing enforcement mode from %s to %s may change how annotations are handled",
			oldPolicy.Spec.GetEnforcement(), newPolicy.Spec.GetEnforcement(),
		))
	}

	// Run same validations as create
	createWarnings, err := v.ValidateCreate(ctx, newObj)
	warnings = append(warnings, createWarnings...)
	return warnings, err
}

// ValidateDelete implements the CustomValidator interface
func (v *AvailabilityPolicyCustomValidator) ValidateDelete(ctx context.Context, obj runtime.Object) (admission.Warnings, error) {
	r, ok := obj.(*AvailabilityPolicy)
	if !ok {
		return nil, fmt.Errorf("expected an AvailabilityPolicy object but got %T", obj)
	}

	availabilitypolicylog.Info("validate delete", "name", r.Name)

	warnings := admission.Warnings{
		"Deleting this policy will remove PDB management from all matching deployments. Ensure alternative policies are in place if needed.",
	}

	return warnings, nil
}

// Validation helper methods

func validateAvailabilityClass(r *AvailabilityPolicy) *field.Error {
	validClasses := map[AvailabilityClass]bool{
		NonCritical:      true,
		Standard:         true,
		HighAvailability: true,
		MissionCritical:  true,
		Custom:           true,
	}

	if !validClasses[r.Spec.AvailabilityClass] {
		return field.Invalid(
			field.NewPath("spec", "availabilityClass"),
			r.Spec.AvailabilityClass,
			"must be one of: non-critical, standard, high-availability, mission-critical, custom",
		)
	}

	// Custom class requires custom config
	if r.Spec.AvailabilityClass == Custom {
		if r.Spec.CustomPDBConfig == nil {
			return field.Required(
				field.NewPath("spec", "customPDBConfig"),
				"custom availability class requires customPDBConfig",
			)
		}

		// Validate custom config
		if r.Spec.CustomPDBConfig.MinAvailable == nil && r.Spec.CustomPDBConfig.MaxUnavailable == nil {
			return field.Invalid(
				field.NewPath("spec", "customPDBConfig"),
				r.Spec.CustomPDBConfig,
				"must specify either minAvailable or maxUnavailable",
			)
		}

		if r.Spec.CustomPDBConfig.MinAvailable != nil && r.Spec.CustomPDBConfig.MaxUnavailable != nil {
			return field.Invalid(
				field.NewPath("spec", "customPDBConfig"),
				r.Spec.CustomPDBConfig,
				"cannot specify both minAvailable and maxUnavailable",
			)
		}
	}

	return nil
}

func validateComponentSelector(r *AvailabilityPolicy) *field.Error {
	selector := r.Spec.ComponentSelector

	// Ensure at least one selection criteria
	hasSelection := len(selector.ComponentNames) > 0 ||
		len(selector.ComponentFunctions) > 0 ||
		len(selector.MatchLabels) > 0 ||
		len(selector.MatchExpressions) > 0

	if !hasSelection {
		return field.Required(
			field.NewPath("spec", "componentSelector"),
			"must specify at least one selection criteria (componentNames, componentFunctions, matchLabels, or matchExpressions)",
		)
	}

	// Validate component functions
	validFunctions := map[ComponentFunction]bool{
		CoreFunction:       true,
		ManagementFunction: true,
		SecurityFunction:   true,
	}

	for i, function := range selector.ComponentFunctions {
		if !validFunctions[function] {
			return field.Invalid(
				field.NewPath("spec", "componentSelector", "componentFunctions").Index(i),
				function,
				"must be one of: core, management, security",
			)
		}
	}

	return nil
}

func validateMaintenanceWindow(window MaintenanceWindow, fldPath *field.Path) field.ErrorList {
	var allErrs field.ErrorList

	// Validate time format
	if _, err := time.Parse("15:04", window.Start); err != nil {
		allErrs = append(allErrs, field.Invalid(
			fldPath.Child("start"),
			window.Start,
			"must be in HH:MM format",
		))
	}

	if _, err := time.Parse("15:04", window.End); err != nil {
		allErrs = append(allErrs, field.Invalid(
			fldPath.Child("end"),
			window.End,
			"must be in HH:MM format",
		))
	}

	// Validate timezone
	if window.Timezone != "" {
		if _, err := time.LoadLocation(window.Timezone); err != nil {
			allErrs = append(allErrs, field.Invalid(
				fldPath.Child("timezone"),
				window.Timezone,
				fmt.Sprintf("invalid timezone: %v", err),
			))
		}
	}

	// Validate days of week
	for i, day := range window.DaysOfWeek {
		if day < 0 || day > 6 {
			allErrs = append(allErrs, field.Invalid(
				fldPath.Child("daysOfWeek").Index(i),
				day,
				"must be between 0 (Sunday) and 6 (Saturday)",
			))
		}
	}

	// Check for duplicate days
	daySet := make(map[int]bool)
	for _, day := range window.DaysOfWeek {
		if daySet[day] {
			allErrs = append(allErrs, field.Duplicate(
				fldPath.Child("daysOfWeek"),
				day,
			))
		}
		daySet[day] = true
	}

	return allErrs
}

func validateEnforcementConfiguration(r *AvailabilityPolicy) field.ErrorList {
	var allErrs field.ErrorList
	specPath := field.NewPath("spec")

	// Validate enforcement mode
	validModes := map[EnforcementMode]bool{
		EnforcementStrict:   true,
		EnforcementFlexible: true,
		EnforcementAdvisory: true,
	}

	if r.Spec.Enforcement != "" && !validModes[r.Spec.Enforcement] {
		allErrs = append(allErrs, field.Invalid(
			specPath.Child("enforcement"),
			r.Spec.Enforcement,
			"must be one of: strict, flexible, advisory",
		))
	}

	// Validate MinimumClass for flexible enforcement
	if r.Spec.Enforcement == EnforcementFlexible && r.Spec.MinimumClass != "" {
		validClasses := map[AvailabilityClass]bool{
			NonCritical:      true,
			Standard:         true,
			HighAvailability: true,
			MissionCritical:  true,
			Custom:           true,
		}

		if !validClasses[r.Spec.MinimumClass] {
			allErrs = append(allErrs, field.Invalid(
				specPath.Child("minimumClass"),
				r.Spec.MinimumClass,
				"must be a valid availability class",
			))
		}

		// MinimumClass should not be higher than AvailabilityClass
		if CompareAvailabilityClasses(r.Spec.MinimumClass, r.Spec.AvailabilityClass) > 0 {
			allErrs = append(allErrs, field.Invalid(
				specPath.Child("minimumClass"),
				r.Spec.MinimumClass,
				"minimumClass cannot be higher than availabilityClass",
			))
		}
	}

	// Validate override configuration for advisory mode
	if r.Spec.Enforcement == EnforcementAdvisory {
		if r.Spec.OverrideRequiresAnnotation != "" && r.Spec.AllowOverride != nil && !*r.Spec.AllowOverride {
			allErrs = append(allErrs, field.Invalid(
				specPath.Child("overrideRequiresAnnotation"),
				r.Spec.OverrideRequiresAnnotation,
				"cannot require annotation when AllowOverride is false",
			))
		}
	}

	// Validate that certain fields are only meaningful for advisory enforcement
	if r.Spec.Enforcement != EnforcementAdvisory {
		if r.Spec.OverrideRequiresAnnotation != "" {
			allErrs = append(allErrs, field.Invalid(
				specPath.Child("overrideRequiresAnnotation"),
				r.Spec.OverrideRequiresAnnotation,
				"only applicable for advisory enforcement mode",
			))
		}

		if r.Spec.OverrideRequiresReason != nil && *r.Spec.OverrideRequiresReason {
			allErrs = append(allErrs, field.Invalid(
				specPath.Child("overrideRequiresReason"),
				r.Spec.OverrideRequiresReason,
				"only applicable for advisory enforcement mode",
			))
		}
	}

	return allErrs
}

// HasSelectionCriteria checks if the ComponentSelector has at least one selection criteria defined
func (s *ComponentSelector) HasSelectionCriteria() bool {
	return len(s.ComponentNames) > 0 ||
		len(s.ComponentFunctions) > 0 ||
		len(s.MatchLabels) > 0 ||
		len(s.MatchExpressions) > 0
}
