package org.tmforum.oda.canvas.portal.helm.client;

import com.google.common.base.Splitter;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;

import org.apache.commons.compress.archivers.ArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;
import org.apache.commons.compress.compressors.gzip.GzipCompressorInputStream;
import org.apache.commons.lang3.StringUtils;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;

/**
 * Utility class
 *
 * @author li.peilong
 * @date 2022/12/09
 */
public abstract class HelmClientUtil {
    /**
     * Whether the current system is Windows
     *
     * @return
     */
    public static boolean isWindows() {
        return StringUtils.containsIgnoreCase(System.getProperty("os.name"), "windows");
    }

    /**
     * Get the working directory
     *
     * @return
     */
    public static Path workingDir() {
        Path workingDir = Paths.get(System.getProperty("user.home")).resolve("helm-client");
        return workingDir;
    }

    /**
     * Helm cache directory
     *
     * @return
     */
    public static Path helmCacheDir() {
        return workingDir().resolve(".cache/helm");
    }

    /**
     * Helm configuration directory
     *
     * @return
     */
    public static Path helmConfigDir() {
        return workingDir().resolve(".config/helm");
    }

    /**
     * Helm data directory
     *
     * @return
     */
    public static Path helmDataDir() {
        return workingDir().resolve(".local/share/helm");
    }

    /**
     * Helm plugins directory
     *
     * @return
     */
    public static Path pluginDir() {
        return helmDataDir().resolve("plugins");
    }

    /**
     * The directory for storing downloaded charts
     *
     * @return
     */
    public static Path chartsDownloadDir() {
        return workingDir().resolve("charts");
    }

    /**
     * Charts extraction directory
     *
     * @return
     */
    public static Path chartsUntarDir() {
        return chartsDownloadDir().resolve("untar");
    }

    /**
     * The extraction directory for a specific version of a chart
     *
     * @param name format repoName/chartName
     * @param version
     * @return
     */
    public static Path chartUntarDir(String name, String version) {
        List<String> parts = Splitter.on("/").splitToList(name);
        return chartsUntarDir().resolve(name).resolve(version).resolve(parts.get(1));
    }

    /**
     * Get the temporary directory
     *
     * @return
     */
    public static Path tmpDir() {
        return workingDir().resolve(".tmp");
    }

    /**
     * Create directories
     *
     * @param dir
     * @throws BaseAppException
     */
    public static void createDirectories(Path dir) throws BaseAppException {
        if (Files.exists(dir)) {
            return;
        }
        try {
            Files.createDirectories(dir);
        } catch (Exception e) {
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.HELM_CREATE_DIRECTORY_FAILED, dir.toFile().getAbsolutePath());
        }
    }

    /**
     * Uncompress tar.gz files
     *
     * @param in
     * @param destPath
     * @throws BaseAppException
     */
    public static void tgzUncompress(InputStream in, Path destPath) throws BaseAppException {
        tgzUncompress(in, destPath, false);
    }

    /**
     * Uncompress tar.gz files
     *
     * @param in
     * @param destPath The target directory
     * @param ignoreDirectory Whether to ignore directories, if set to true, the files in the archive will be directly extracted to the destPath directory
     */
    public static void tgzUncompress(InputStream in, Path destPath, Boolean ignoreDirectory) throws BaseAppException {
        try (BufferedInputStream bin = new BufferedInputStream(in);
             GzipCompressorInputStream gin = new GzipCompressorInputStream(bin);
             TarArchiveInputStream tin = new TarArchiveInputStream(gin)) {
            if (Files.notExists(destPath)) {
                Files.createDirectories(destPath);
            }
            ArchiveEntry entry;
            while ((entry = tin.getNextEntry()) != null) {
                if (entry.isDirectory()) {
                    Path dirPath = destPath.resolve(entry.getName());
                    if (Files.notExists(dirPath)) {
                        Files.createDirectories(dirPath);
                    }
                    continue;
                }
                Path filePath = null;
                if (ignoreDirectory) {
                    String[] names = entry.getName().split("/");
                    filePath = destPath.resolve(names[names.length - 1]);
                } else {
                    filePath = destPath.resolve(entry.getName());
                    Path parentPath = filePath.getParent();
                    if (parentPath != null && Files.notExists(parentPath)) {
                        Files.createDirectories(parentPath);
                    }
                }
                Files.copy(tin, filePath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.HELM_UNCOMPRESS_FAILED, e.getMessage());
        }
    }

    /**
     * Uncompress tar.gz files
     *
     * @param file
     * @param destPath
     */
    public static void tgzUncompress(File file, Path destPath) throws BaseAppException {
        try {
            FileInputStream in = new FileInputStream(file);
            tgzUncompress(in, destPath);
        } catch (Exception e) {
            ExceptionPublisher.publish(HelmClientExceptionErrorCode.HELM_UNCOMPRESS_FAILED, e.getMessage());
        }
    }

}
