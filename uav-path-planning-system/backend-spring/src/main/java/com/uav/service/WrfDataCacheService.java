package com.uav.service;

import com.uav.config.UavProperties;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.FileTime;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/**
 * WRF 气象数据缓存服务。
 * <p>
 * 从本地文件系统加载 WRF NetCDF 数据文件，缓存最新的气象数据快照。
 * 由 {@link WrfUpdateScheduler} 定时触发更新。
 * </p>
 */
@Slf4j
@Service
public class WrfDataCacheService {

    private final UavProperties uavProperties;

    /** 最新的 WRF 数据快照（按变量名索引） */
    private final Map<String, Object> dataCache = new ConcurrentHashMap<>();

    /** 数据文件最后修改时间 */
    private final AtomicReference<FileTime> lastModified = new AtomicReference<>(null);

    /** 缓存命中次数 */
    private final AtomicLong hitCount = new AtomicLong(0);

    /** 缓存更新次数 */
    private final AtomicLong updateCount = new AtomicLong(0);

    /** 标记是否有可用数据 */
    private volatile boolean dataAvailable = false;

    /** 上次成功更新时间 */
    private volatile LocalDateTime lastUpdateTime = null;

    public WrfDataCacheService(UavProperties uavProperties) {
        this.uavProperties = uavProperties;
    }

    @PostConstruct
    public void init() {
        log.info("WRF 数据缓存服务初始化，数据路径: {}", uavProperties.getWrf().getDataPath());
        Path dataDir = Paths.get(uavProperties.getWrf().getDataPath());
        if (Files.exists(dataDir)) {
            log.info("WRF 数据目录已存在: {}", dataDir.toAbsolutePath());
        } else {
            log.warn("WRF 数据目录不存在，将在首次更新时创建: {}", dataDir.toAbsolutePath());
        }
    }

    /**
     * 从文件系统刷新 WRF 数据缓存。
     * 由 {@link WrfUpdateScheduler#updateWrfData()} 定时调用。
     */
    public synchronized void refresh() {
        Path dataDir = Paths.get(uavProperties.getWrf().getDataPath());
        try {
            // 确保目录存在
            Files.createDirectories(dataDir);

            // 查找最新的 WRF 数据文件（.nc 或 .h5 格式）
            Optional<Path> latestFile = findLatestFile(dataDir);

            if (latestFile.isPresent()) {
                Path file = latestFile.get();
                FileTime fileModTime = Files.getLastModifiedTime(file);

                // 只处理更新的文件
                FileTime prev = lastModified.get();
                if (prev != null && fileModTime.compareTo(prev) <= 0) {
                    log.debug("WRF 数据文件无变化，跳过更新: {}", file.getFileName());
                    hitCount.incrementAndGet();
                    return;
                }

                // 加载数据到缓存
                loadFileToCache(file);
                lastModified.set(fileModTime);
                dataAvailable = true;
                lastUpdateTime = LocalDateTime.now();
                updateCount.incrementAndGet();

                log.info("WRF 数据缓存已更新: {} ({} 次更新)", file.getFileName(), updateCount.get());
            } else {
                log.warn("未找到 WRF 数据文件，使用默认数据路径: {}", dataDir);
                // 生成默认数据占位
                generateDefaultData();
                dataAvailable = false;
            }
        } catch (IOException e) {
            log.error("WRF 数据更新失败: {}", e.getMessage());
        }
    }

    /**
     * 查找数据目录中最新的 WRF 文件。
     */
    private Optional<Path> findLatestFile(Path dir) throws IOException {
        Path latest = null;
        FileTime latestTime = null;

        // 支持的文件格式
        String[] extensions = { ".nc", ".netcdf", ".h5", ".hdf5", ".grib2", ".json", ".csv" };

        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
            for (Path entry : stream) {
                if (Files.isRegularFile(entry)) {
                    String name = entry.getFileName().toString().toLowerCase();
                    for (String ext : extensions) {
                        if (name.endsWith(ext)) {
                            FileTime fileTime = Files.getLastModifiedTime(entry);
                            if (latest == null || fileTime.compareTo(latestTime) > 0) {
                                latest = entry;
                                latestTime = fileTime;
                            }
                            break;
                        }
                    }
                }
            }
        }

        return Optional.ofNullable(latest);
    }

    /**
     * 将 WRF 文件加载到缓存。
     * <p>
     * 对于 NetCDF 文件，解析关键变量到内存 Map。
     * 对于非 NetCDF 文件，记录文件元信息。
     * </p>
     */
    private void loadFileToCache(Path file) {
        String fileName = file.getFileName().toString();
        String fileExt = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();

        dataCache.put("_file", fileName);
        dataCache.put("_filePath", file.toAbsolutePath().toString());
        dataCache.put("_fileSize", file.toFile().length());
        dataCache.put("_timestamp", System.currentTimeMillis());

        switch (fileExt) {
            case "nc":
            case "netcdf":
                loadNetCdfFile(file);
                break;
            case "json":
                loadJsonFile(file);
                break;
            case "csv":
                loadCsvFile(file);
                break;
            default:
                log.info("WRF 文件类型 {} 暂不支持解析，仅记录元信息", fileExt);
                break;
        }
    }

    /**
     * 解析 NetCDF 文件（python 脚本处理，Java 侧记录文件路径）。
     */
    private void loadNetCdfFile(Path file) {
        dataCache.put("_format", "netcdf");
        dataCache.put("_status", "pending_parse");
        dataCache.put("_parser", "wrf_processor.py");
    }

    /**
     * 解析 JSON 格式的 WRF 数据。
     */
    private void loadJsonFile(Path file) {
        try {
            String content = Files.readString(file);
            dataCache.put("_format", "json");
            dataCache.put("_raw", content);
            dataCache.put("_status", "loaded");
        } catch (IOException e) {
            log.warn("无法读取 JSON 文件: {}", file, e);
        }
    }

    /**
     * 解析 CSV 格式的 WRF 数据。
     */
    private void loadCsvFile(Path file) {
        try {
            long lines = Files.lines(file).count();
            dataCache.put("_format", "csv");
            dataCache.put("_rowCount", lines);
            dataCache.put("_status", "loaded");
        } catch (IOException e) {
            log.warn("无法读取 CSV 文件: {}", file, e);
        }
    }

    /**
     * 生成默认数据（当目录为空时）。
     */
    private void generateDefaultData() {
        dataCache.put("_status", "default");
        dataCache.put("_format", "none");
        dataCache.put("_note", "无可用数据文件，使用默认值");
    }

    // ─── 公开查询方法 ──────────────────────────────────────────────

    /**
     * 获取缓存的 WRF 数据快照。
     */
    public Map<String, Object> getDataSnapshot() {
        hitCount.incrementAndGet();
        return Map.copyOf(dataCache);
    }

    /**
     * 获取指定变量的缓存值。
     */
    @SuppressWarnings("unchecked")
    public <T> T getData(String key) {
        hitCount.incrementAndGet();
        return (T) dataCache.get(key);
    }

    /**
     * 检查是否有可用数据。
     */
    public boolean isDataAvailable() {
        return dataAvailable;
    }

    /**
     * 获取缓存统计信息。
     */
    public Map<String, Object> getCacheStats() {
        return Map.of(
                "dataAvailable", dataAvailable,
                "cachedVariables", dataCache.size(),
                "hitCount", hitCount.get(),
                "updateCount", updateCount.get(),
                "lastUpdate", lastUpdateTime != null ? lastUpdateTime.toString() : "never",
                "dataPath", uavProperties.getWrf().getDataPath()
        );
    }

    /**
     * 获取自上次更新以来的时间。
     */
    public Duration timeSinceLastUpdate() {
        if (lastUpdateTime == null) {
            return Duration.ofDays(365);
        }
        return Duration.between(lastUpdateTime, LocalDateTime.now());
    }
}
