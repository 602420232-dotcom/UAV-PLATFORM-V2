package com.wrf.processor.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public class PythonExecutor {

    private static final Logger log = LoggerFactory.getLogger(PythonExecutor.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static Map<String, Object> execute(String pythonScript, String action, Map<String, Object> request) {
        Path tempFile = null;
        try {
            tempFile = Files.createTempFile("python_", ".json");
            objectMapper.writeValue(tempFile.toFile(), request);

            ProcessBuilder pb = new ProcessBuilder("python3", pythonScript, action, tempFile.toString());
            pb.redirectErrorStream(true);
            Process process = pb.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            StringBuilder output = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
            }

            int exitCode = process.waitFor();
            return Map.of("success", exitCode == 0, "data", output.toString());

        } catch (Exception e) {
            log.error("Python 脚本执行失败: {} {}: {}", pythonScript, action, e.getMessage());
            return Map.of("success", false, "error", "处理失败");
        } finally {
            if (tempFile != null) {
                try { Files.deleteIfExists(tempFile); } catch (Exception ignored) {}
            }
        }
    }
}
