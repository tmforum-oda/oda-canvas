package org.tmforum.oda.canvas.portal.component;

public class ComponentVersions {
    private static final String[] SUPPORTED_VERSIONS = new String[]{
        "v1", "v1beta4", "v1beta3", "v1beta1", "v1alpha4", "v1alpha3", "v1alpha2", "v1alpha1"
    };

    // Getter for SUPPORTED_VERSIONS
    public static String[] getSupportedVersions() {
        return SUPPORTED_VERSIONS.clone(); // Return a clone to ensure immutability
    }
}