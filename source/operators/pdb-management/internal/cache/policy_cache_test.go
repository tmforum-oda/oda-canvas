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
