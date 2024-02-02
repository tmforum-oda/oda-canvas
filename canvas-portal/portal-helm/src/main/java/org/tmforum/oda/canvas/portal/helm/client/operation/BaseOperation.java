package org.tmforum.oda.canvas.portal.helm.client.operation;

import com.google.common.base.Joiner;
import com.google.common.base.Splitter;
import com.google.common.base.Stopwatch;
import com.google.common.util.concurrent.ThreadFactoryBuilder;
import org.tmforum.oda.canvas.portal.helm.client.HelmClientExceptionErrorCode;
import org.tmforum.oda.canvas.portal.core.exception.BaseAppException;
import org.tmforum.oda.canvas.portal.core.exception.ExceptionPublisher;
import org.tmforum.oda.canvas.portal.core.util.StringUtil;


import org.tmforum.oda.canvas.portal.helm.client.HelmClientUtil;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.time.DateFormatUtils;
import org.apache.commons.lang3.time.DateUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Provides some common methods
 *
 * @author li.peilong
 * @date 2022/12/06
 */
public abstract class BaseOperation {
    private static final Logger LOGGER = LoggerFactory.getLogger(BaseOperation.class);
    private static final ExecutorService POOL = new ThreadPoolExecutor(5, 10,
            0L, TimeUnit.MILLISECONDS, new LinkedBlockingQueue<>(20), new ThreadFactoryBuilder()
            .setNameFormat("helm-result-reader-%d").setDaemon(true).build());

    /**
     * Execute helm command
     *
     * @param cmd command to execute
     * @return command execute result
     * @throws BaseAppException if exec operation failed
     */
    protected String exec(String cmd) throws BaseAppException {
        return exec(cmd, 300);
    }

    /**
     * Execute helm command
     *
     * @param cmd     command to execute
     * @param timeout Command execution timeout in seconds
     * @return Returns the result of the helm command
     */
    protected String exec(String cmd, int timeout) throws BaseAppException {
        String[] cmds = fullCmd(cmd);
        StringBuilder stdout = new StringBuilder();
        StringBuilder stderr = new StringBuilder();
        Process process = null;
        int exitCode = 0;
        Stopwatch stopwatch = Stopwatch.createStarted();
        try {
            LOGGER.debug("Execute command [{}]", Joiner.on(" ").join(cmds));
            // Start the command
            ProcessBuilder pb = new ProcessBuilder(cmds);
            // Set the paths for helm data, configuration, etc.
            if (!HelmClientUtil.isWindows()) {
                pb.environment().put("HELM_CACHE_HOME", HelmClientUtil.helmCacheDir().toFile().getAbsolutePath());
                pb.environment().put("HELM_CONFIG_HOME", HelmClientUtil.helmConfigDir().toFile().getAbsolutePath());
                pb.environment().put("HELM_DATA_HOME", HelmClientUtil.helmDataDir().toFile().getAbsolutePath());
            }
            process = pb.start();
            // Read command return information and error information
            readProcessOutput(stdout, stderr, process, timeout);
            exitCode = process.waitFor();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to execute command [{}], error: ", Joiner.on(" ").join(cmds), e);
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.EXEC_OPERATION_FAILED, cmd, e.getMessage());
        }
        finally {
            if (process != null) {
                process.destroy();
            }
            long cost = stopwatch.stop().elapsed(TimeUnit.MILLISECONDS);
            LOGGER.debug("Execute command [{}] cost {}ms", Joiner.on(" ").join(cmds), cost);
        }
        if (exitCode != 0) {
            LOGGER.warn("Failed to execute command [{}], error: {}", Joiner.on(" ").join(cmds), stderr.toString());
            ExceptionPublisher.publish(HelmClientExceptionErrorCode.EXEC_OPERATION_FAILED, cmd, stderr.toString());
        }
        LOGGER.debug("Execute command [{}] successfully, result: [{}]", Joiner.on(" ").join(cmds), stdout.toString());
        return StringUtils.strip(stdout.toString(), "\n");
    }

    /**
     * Get the full command, mainly to concatenate the absolute address of the helm command file
     *
     * @param cmd command to execute
     * @return the full command
     */
    private String[] fullCmd(String cmd) {
        if (HelmClientUtil.isWindows()) {
            return new String[]{"cmd", "/c", StringUtil.format("{}/{}", HelmClientUtil.workingDir(), cmd)};
        }
        return new String[]{"sh", "-c", StringUtil.format("{}/{}", HelmClientUtil.workingDir(), cmd)};
    }

    /**
     * Write text to a file
     *
     * @param text text
     * @param extension File extension, such as yaml
     * @return the file path
     */
    protected String writeToFile(String text, String extension) throws BaseAppException {
        Path dir = HelmClientUtil.tmpDir();
        String fileName = StringUtil.format("{}-{}.{}",
                "helm-" + UUID.randomUUID(),
                DateFormatUtils.format(new Date(), "yyyyMMdd"),
                StringUtils.isNoneBlank(extension) ? StringUtils.strip(extension, ".") : "dat");
        File tmpFile = new File(dir.toFile(), fileName);
        try {
            if (Files.notExists(dir)) {
                Files.createDirectories(dir);
            }
            // Write text to temporary file
            FileUtils.writeStringToFile(tmpFile, text, StandardCharsets.UTF_8);
            return tmpFile.getAbsolutePath();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to write [{}] to file [{}], error:", text, tmpFile.getAbsolutePath(), e);
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.WRITE_TMP_FILE_FAILED, tmpFile.getAbsolutePath(), e.getMessage());
        }
        finally {
            // Attempt to clean up historical temporary files first
            cleanTmpFiles();
        }
        return "";

    }

    /**
     * Get the repository name
     *
     * @param name Format repoName/chartName
     * @return repository name
     */
    public String getRepoName(String name) {
        return Splitter.on("/").splitToList(name).get(0);
    }

    /**
     * Clean up generated temporary files
     *
     */
    private void cleanTmpFiles() {
        try {
            Collection<File> files = FileUtils.listFiles(HelmClientUtil.tmpDir().toFile(), null, false);
            files.stream()
                    .filter(file -> FileUtils.isFileOlder(file, DateUtils.addDays(new Date(), -3)))
                    .forEach(FileUtils::deleteQuietly);
        }
        catch (Exception e) {
            LOGGER.warn("Failed to clean tmp files, error:", e);
        }

    }

    /**
     * Read helm command output
     *
     * @param stdout  stdout
     * @param stderr  stderr
     * @param process process which execute command
     * @throws InterruptedException if thre
     * @throws BaseAppException if the read operation failed
     */
    private static void readProcessOutput(StringBuilder stdout, StringBuilder stderr, Process process, int timeout) throws InterruptedException, BaseAppException {
        CountDownLatch latch = new CountDownLatch(2);
        // Read standard error output
        POOL.execute(() -> {
                    try {
                        int c;
                        while ((c = process.getErrorStream().read()) != -1) {
                            stderr.append((char) c);
                        }
                    }
                    catch (Exception e) {
                        LOGGER.error("process exec failed", e);
                    }
                    finally {
                        latch.countDown();
                    }
                }
        );
        // Read standard output
        POOL.execute(() -> {
            try {
                int c;
                while ((c = process.getInputStream().read()) != -1) {
                    stdout.append((char) c);
                }
            }
            catch (Exception e) {
                LOGGER.error("process exec failed", e);
            }
            finally {
                latch.countDown();
            }
        });
        // Wait for reading to end
        boolean result = latch.await(timeout, TimeUnit.SECONDS);
        if (!result) {
            ExceptionPublisher.publish(HelmClientExceptionErrorCode.EXEC_OPERATION_TIMEOUT);
        }
    }

}
