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
 * 提供一些公共方法
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
     * 执行helm命令
     *
     * @param cmd
     * @return
     * @throws BaseAppException
     */
    protected String exec(String cmd) throws BaseAppException {
        return exec(cmd, 300);
    }

    /**
     * 执行helm命令
     * @param cmd
     * @param timeout 命令执行超时时间，单位：秒
     *
     * @return 返回helm命令结果
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
            // 启动命令
            ProcessBuilder pb = new ProcessBuilder(cmds);
            // 设置helm的数据、配置等路径
            if (!HelmClientUtil.isWindows()) {
                pb.environment().put("HELM_CACHE_HOME", HelmClientUtil.helmCacheDir().toFile().getAbsolutePath());
                pb.environment().put("HELM_CONFIG_HOME", HelmClientUtil.helmConfigDir().toFile().getAbsolutePath());
                pb.environment().put("HELM_DATA_HOME", HelmClientUtil.helmDataDir().toFile().getAbsolutePath());
            }
            process = pb.start();
            // 读取命令返回信息和错误信息
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
     * 获取完整的命令，主要是拼接helm命令文件的绝对地址
     *
     * @param cmd
     * @return
     */
    private String[] fullCmd(String cmd) {
        if (HelmClientUtil.isWindows()) {
            return new String[]{"cmd", "/c", StringUtil.format("{}/{}", HelmClientUtil.workingDir(), cmd)};
        }
        return new String[]{"sh", "-c", StringUtil.format("{}/{}", HelmClientUtil.workingDir(), cmd)};
    }

    /**
     * 将文本写入到文件中
     *
     * @param text
     * @param extension 文件扩展名，比如yaml
     * @return
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
            // 将文本写入临时文件
            FileUtils.writeStringToFile(tmpFile, text, StandardCharsets.UTF_8);
            return tmpFile.getAbsolutePath();
        }
        catch (Exception e) {
            LOGGER.warn("Failed to write [{}] to file [{}], error:", text, tmpFile.getAbsolutePath(), e);
            ExceptionPublisher.publish(e, HelmClientExceptionErrorCode.WRITE_TMP_FILE_FAILED, tmpFile.getAbsolutePath(), e.getMessage());
        }
        finally {
            // 先尝试清理历史临时文件
            cleanTmpFiles();
        }
        return "";

    }

    /**
     * 获取仓库名称
     *
     * @param name 格式repoName/chartName
     * @return
     */
    public String getRepoName(String name) {
        return Splitter.on("/").splitToList(name).get(0);
    }

    /**
     * 清理生成的临时文件
     *
     */
    private void cleanTmpFiles() {
        try {
            Collection<File> files = FileUtils.listFiles(HelmClientUtil.tmpDir().toFile(), null, false);
            files.stream()
                    .filter(file -> FileUtils.isFileOlder(file, DateUtils.addDays(new Date(), -3)))
                    .forEach(file -> FileUtils.deleteQuietly(file));
        }
        catch (Exception e) {
            LOGGER.warn("Failed to clean tmp files, error:", e);
        }

    }

    /**
     * 读取helm命令输出
     *
     * @param stdout
     * @param stderr
     * @param process
     * @throws InterruptedException
     * @throws BaseAppException
     */
    private static void readProcessOutput(StringBuilder stdout, StringBuilder stderr, Process process, int timeout) throws InterruptedException, BaseAppException {
        CountDownLatch latch = new CountDownLatch(2);
        // 读取标准错误输出
        POOL.execute(() -> {
                    try {
                        int c;
                        while ((c = process.getErrorStream().read()) != -1) {
                            stderr.append((char) c);
                        }
                    }
                    catch (Exception e) {
                        //FIXME
                        //LOGGER.error(e);
                    }
                    finally {
                        latch.countDown();
                    }
                }
        );
        // 读取标准输出
        POOL.execute(() -> {
            try {
                int c;
                while ((c = process.getInputStream().read()) != -1) {
                    stdout.append((char) c);
                }
            }
            catch (Exception e) {
                //FIXME
                // LOGGER.error(e);
            }
            finally {
                latch.countDown();
            }
        });
        // 等待读取结束
        boolean result = latch.await(timeout, TimeUnit.SECONDS);
        if (!result) {
            ExceptionPublisher.publish(HelmClientExceptionErrorCode.EXEC_OPERATION_TIMEOUT);
        }
    }

}
