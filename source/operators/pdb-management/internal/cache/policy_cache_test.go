package cache

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	availabilityv1alpha1 "github.com/tmforum-oda/oda-canvas/source/operators/pdb-management/api/v1alpha1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func newTestPolicy(name, ns string) *availabilityv1alpha1.AvailabilityPolicy {
	return &availabilityv1alpha1.AvailabilityPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: ns,
		},
		Spec: availabilityv1alpha1.AvailabilityPolicySpec{
			AvailabilityClass: availabilityv1alpha1.Standard,
		},
	}
}

func TestPolicyCache_GetSet(t *testing.T) {
	cache := NewPolicyCache(2, 50*time.Millisecond)
	p := newTestPolicy("foo", "ns")
	cache.Set("foo", p)
	got, ok := cache.Get("foo")
	assert.True(t, ok)
	assert.Equal(t, "foo", got.Name)
	// Expiry
	time.Sleep(60 * time.Millisecond)
	_, ok = cache.Get("foo")
	assert.False(t, ok)
}

func TestPolicyCache_GetList_SetList(t *testing.T) {
	cache := NewPolicyCache(2, 50*time.Millisecond)
	p1 := *newTestPolicy("foo", "ns")
	p2 := *newTestPolicy("bar", "ns")
	cache.SetList("all", []availabilityv1alpha1.AvailabilityPolicy{p1, p2})
	list, ok := cache.GetList("all")
	assert.True(t, ok)
	assert.Len(t, list, 2)
	assert.Equal(t, "foo", list[0].Name)
	// Expiry
	time.Sleep(60 * time.Millisecond)
	_, ok = cache.GetList("all")
	assert.False(t, ok)
}

func TestPolicyCache_MaintenanceWindow(t *testing.T) {
	cache := NewPolicyCache(2, 10*time.Millisecond)
	cache.SetMaintenanceWindow("mw", true, 10*time.Millisecond)
	val, ok := cache.GetMaintenanceWindow("mw")
	assert.True(t, ok)
	assert.True(t, val)
	// The cache uses a hardcoded 1 minute TTL, so the value should remain for at least that long
}

func TestPolicyCache_Delete_Clear_Stop(t *testing.T) {
	cache := NewPolicyCache(2, 100*time.Millisecond)
	p := newTestPolicy("foo", "ns")
	cache.Set("foo", p)
	cache.Delete("foo")
	_, ok := cache.Get("foo")
	assert.False(t, ok)
	p2 := newTestPolicy("bar", "ns")
	cache.Set("bar", p2)
	cache.Clear()
	_, ok = cache.Get("bar")
	assert.False(t, ok)
	cache.Stop() // should not panic
}

func TestPolicyCache_EvictOldest(t *testing.T) {
	cache := NewPolicyCache(2, 1*time.Second)
	p1 := newTestPolicy("foo", "ns")
	p2 := newTestPolicy("bar", "ns")
	p3 := newTestPolicy("baz", "ns")
	cache.Set("foo", p1)
	cache.Set("bar", p2)
	cache.Set("baz", p3) // should evict one
	// Only 2 entries should remain
	count := 0
	for _, k := range []string{"foo", "bar", "baz"} {
		if _, ok := cache.Get(k); ok {
			count++
		}
	}
	assert.Equal(t, 2, count)
}

func TestPolicyCache_Stats(t *testing.T) {
	cache := NewPolicyCache(2, 1*time.Second)
	p := newTestPolicy("foo", "ns")
	cache.Set("foo", p)
	cache.Get("foo")
	cache.Get("bar")
	stats := cache.GetStats()
	assert.GreaterOrEqual(t, stats.Hits, int64(1))
	assert.GreaterOrEqual(t, stats.Misses, int64(1))
}

func TestNewPolicyCacheWithConfig(t *testing.T) {
	config := CacheConfig{
		MaxSize:              5,
		PolicyTTL:            2 * time.Minute,
		MaintenanceWindowTTL: 30 * time.Second,
	}
	cache := NewPolicyCacheWithConfig(config)
	defer cache.Stop()

	assert.NotNil(t, cache)
	assert.Equal(t, 5, cache.maxSize)
	assert.Equal(t, 2*time.Minute, cache.ttl)
	assert.Equal(t, 30*time.Second, cache.maintenanceTTL)
}

func TestDefaultCacheConfig(t *testing.T) {
	config := DefaultCacheConfig()
	assert.Equal(t, 100, config.MaxSize)
	assert.Equal(t, 5*time.Minute, config.PolicyTTL)
	assert.Equal(t, 1*time.Minute, config.MaintenanceWindowTTL)
}

func TestPolicyCache_InvalidatePolicy(t *testing.T) {
	cache := NewPolicyCache(10, 5*time.Minute)
	defer cache.Stop()

	// Set up cache with some entries
	p1 := newTestPolicy("policy1", "ns1")
	p2 := newTestPolicy("policy2", "ns1")
	cache.Set("ns1/policy1", p1)
	cache.Set("ns1/policy2", p2)
	cache.SetList("all-policies", []availabilityv1alpha1.AvailabilityPolicy{*p1, *p2})
	cache.SetMaintenanceWindow("ns1/deploy1", true, time.Minute)

	// Verify entries exist
	_, ok := cache.Get("ns1/policy1")
	assert.True(t, ok, "policy1 should exist before invalidation")
	_, ok = cache.GetList("all-policies")
	assert.True(t, ok, "all-policies list should exist before invalidation")

	// Invalidate policy1
	cache.InvalidatePolicy("ns1/policy1")

	// Verify policy1 is removed
	_, ok = cache.Get("ns1/policy1")
	assert.False(t, ok, "policy1 should be removed after invalidation")

	// Verify all-policies list is invalidated
	_, ok = cache.GetList("all-policies")
	assert.False(t, ok, "all-policies list should be invalidated")

	// Verify maintenance cache is cleared
	_, ok = cache.GetMaintenanceWindow("ns1/deploy1")
	assert.False(t, ok, "maintenance window should be invalidated")

	// Verify other policy still exists
	_, ok = cache.Get("ns1/policy2")
	assert.True(t, ok, "policy2 should still exist")
}

func TestPolicyCache_InvalidateByNamespace(t *testing.T) {
	cache := NewPolicyCache(10, 5*time.Minute)
	defer cache.Stop()

	// Set up cache with entries from multiple namespaces
	p1 := newTestPolicy("policy1", "ns1")
	p2 := newTestPolicy("policy2", "ns1")
	p3 := newTestPolicy("policy3", "ns2")
	cache.Set("ns1/policy1", p1)
	cache.Set("ns1/policy2", p2)
	cache.Set("ns2/policy3", p3)
	cache.SetList("all-policies", []availabilityv1alpha1.AvailabilityPolicy{*p1, *p2, *p3})

	// Verify entries exist
	_, ok := cache.Get("ns1/policy1")
	assert.True(t, ok)
	_, ok = cache.Get("ns1/policy2")
	assert.True(t, ok)
	_, ok = cache.Get("ns2/policy3")
	assert.True(t, ok)

	// Invalidate namespace ns1
	cache.InvalidateByNamespace("ns1")

	// Verify ns1 policies are removed
	_, ok = cache.Get("ns1/policy1")
	assert.False(t, ok, "ns1/policy1 should be removed")
	_, ok = cache.Get("ns1/policy2")
	assert.False(t, ok, "ns1/policy2 should be removed")

	// Verify ns2 policy still exists
	_, ok = cache.Get("ns2/policy3")
	assert.True(t, ok, "ns2/policy3 should still exist")

	// Verify all-policies list is invalidated
	_, ok = cache.GetList("all-policies")
	assert.False(t, ok, "all-policies list should be invalidated")
}

func TestPolicyCache_ConfigurableMaintenanceTTL(t *testing.T) {
	// Create cache with short maintenance TTL
	config := CacheConfig{
		MaxSize:              10,
		PolicyTTL:            5 * time.Minute,
		MaintenanceWindowTTL: 50 * time.Millisecond,
	}
	cache := NewPolicyCacheWithConfig(config)
	defer cache.Stop()

	// Set maintenance window
	cache.SetMaintenanceWindow("test-key", true, time.Minute)

	// Should be available immediately
	val, ok := cache.GetMaintenanceWindow("test-key")
	assert.True(t, ok, "maintenance window should be found")
	assert.True(t, val, "maintenance window value should be true")

	// Wait for TTL to expire
	time.Sleep(60 * time.Millisecond)

	// Should be expired
	_, ok = cache.GetMaintenanceWindow("test-key")
	assert.False(t, ok, "maintenance window should be expired")
}
