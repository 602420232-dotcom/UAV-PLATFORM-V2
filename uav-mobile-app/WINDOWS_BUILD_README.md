# UAV Path Planning - Windows Desktop Application

## Build Information

**Application Name:** UAV Path Planning
**Version:** 1.0.0+1
**Platform:** Windows Desktop (64-bit)
**Build Date:** June 1, 2026
**Framework:** Flutter 3.41.9

## Executable Location

The standalone Windows executable is located at:

```
uav-mobile-app\build\windows\x64\runner\Release\uav_path_planning_app.exe
```

## System Requirements

### Minimum Requirements
- **Operating System:** Windows 10 (64-bit) or later
- **Processor:** x64 architecture (Intel/AMD)
- **Memory:** 4 GB RAM
- **Storage:** 200 MB free disk space
- **Graphics:** DirectX 11 compatible graphics card

### Recommended Requirements
- **Operating System:** Windows 11 (64-bit)
- **Processor:** Modern multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **Memory:** 8 GB RAM or more
- **Storage:** 500 MB free disk space
- **Graphics:** DirectX 12 compatible graphics card

## Build Components

The release build includes the following components:

### Main Executable
- **uav_path_planning_app.exe** (92 KB)
  - Entry point for the application
  - Includes version information and metadata

### Required DLLs
- **flutter_windows.dll** (20 MB)
  - Core Flutter engine
  - Required for all Flutter applications

- **connectivity_plus_plugin.dll** (98 KB)
  - Network connectivity monitoring
  - Required for checking internet connection status

- **dartjni.dll** (62 KB)
  - Dart runtime support

- **flutter_secure_storage_windows_plugin.dll** (159 KB)
  - Secure local storage for sensitive data
  - Encryption support for credentials

- **permission_handler_windows_plugin.dll** (118 KB)
  - Windows permission management

### Data Directory
Contains Flutter assets and resources:
- Application configuration files
- Material Icons and Cupertino icons
- ICU data for internationalization
- Shader files for UI effects
- Asset manifests

## Deployment Instructions

### Standalone Deployment

To deploy the application on Windows 10 or later:

1. Copy the entire `Release` folder to your target location
2. Ensure all DLL files are in the same directory as the EXE
3. The `data` folder must remain in the same directory structure
4. Run `uav_path_planning_app.exe`

### Directory Structure
```
Release/
├── uav_path_planning_app.exe
├── flutter_windows.dll
├── connectivity_plus_plugin.dll
├── dartjni.dll
├── flutter_secure_storage_windows_plugin.dll
├── permission_handler_windows_plugin.dll
└── data/
    ├── flutter_assets/
    └── icudtl.dat
```

### Installation Package (Optional)

For a proper Windows installation experience:

1. Create an installer using tools like:
   - Inno Setup
   - WiX Toolset
   - NSIS

2. Include all DLL files and the data directory

3. Register application metadata (version, publisher, etc.)

## Features

### Core Features
- ✅ User authentication and session management
- ✅ Responsive UI with Material Design 3
- ✅ Error handling with user-friendly messages
- ✅ Platform detection (shows Windows Desktop indicator)
- ✅ Network connectivity monitoring
- ✅ Secure credential storage

### Windows-Specific Features
- ✅ Native Windows window management (minimize, maximize, close)
- ✅ Windows-specific error handling
- ✅ Desktop-appropriate iconography
- ✅ Optimized for Windows 10/11

## Configuration

### Application Settings
The application reads configuration from:
```
data/flutter_assets/assets/config/app_config.json
```

Default configuration:
```json
{
  "app_name": "UAV Path Planning",
  "version": "1.0.0",
  "api_base_url": "http://localhost:8080",
  "enable_offline_mode": true,
  "max_cache_size_mb": 100,
  "enable_telemetry": false,
  "map_settings": {
    "default_zoom": 10,
    "default_center": {
      "lat": 39.9042,
      "lng": 116.4074
    }
  }
}
```

### Changing API Endpoint
Edit the `api_base_url` in `app_config.json` to point to your backend server.

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
**Symptoms:** Double-clicking the EXE does nothing or shows an error.

**Solutions:**
- Ensure all DLL files are present
- Verify the `data` directory exists with proper structure
- Check Windows Event Viewer for error logs
- Ensure you have Windows 10 or later

#### 2. Missing DLL Errors
**Symptoms:** "The code execution cannot proceed because X.dll was not found"

**Solution:**
- Ensure all DLL files from the Release folder are present
- Copy the entire Release folder, not just the EXE

#### 3. Graphics/Display Issues
**Symptoms:** Application window appears blank or distorted.

**Solutions:**
- Update your graphics drivers
- Ensure DirectX 11 or later is installed
- Try running in compatibility mode (not recommended for production)

#### 4. Network Connection Errors
**Symptoms:** Application shows connection errors or fails to authenticate.

**Solutions:**
- Check if your API server is running
- Verify the `api_base_url` in configuration
- Check Windows Firewall settings
- Ensure internet connectivity

#### 5. Secure Storage Errors
**Symptoms:** Application fails to save credentials or shows encryption errors.

**Solutions:**
- Ensure write permissions to AppData directory
- Check if antivirus is blocking secure storage
- Try running as administrator (not recommended for production)

### Logging

The application uses debug logging in debug builds. In release builds, errors are caught and displayed to users with retry options.

To enable verbose logging:
1. Build with `--verbose` flag
2. Check console output if running from command line
3. Monitor Windows Event Viewer under "Application" logs

## Performance Optimization

### Startup Time
- Release builds use ahead-of-time (AOT) compilation
- Assets are loaded from the bundled `data` directory
- Typical startup time: 1-3 seconds on modern hardware

### Memory Usage
- Baseline memory: ~100-150 MB
- With active operations: ~200-300 MB
- Shared Flutter engine reduces per-app memory footprint

### Disk Space
- Total package size: ~22 MB
- Includes all dependencies and assets
- No additional runtime installation required

## Security Considerations

### Secure Storage
- Credentials are encrypted using Windows DPAPI
- Data is stored in user's AppData directory
- Automatic cleanup on logout

### Network Security
- HTTPS communication recommended for production
- Certificate validation enabled by default
- No hardcoded credentials in the application

### Code Signing
For production deployment, consider signing the executable:
1. Obtain a code signing certificate
2. Sign the EXE and DLL files
3. This prevents Windows SmartScreen warnings

## Testing

### Manual Testing Checklist
- [ ] Application starts without errors
- [ ] Login screen displays correctly
- [ ] Error messages display when API is unavailable
- [ ] Windows desktop indicator appears in UI
- [ ] Logout functionality works
- [ ] Window management (minimize, maximize, close) works
- [ ] Application handles network disconnection gracefully

### Automated Testing
Run Flutter tests:
```bash
cd uav-mobile-app
flutter test
```

### Windows-Specific Testing
```bash
# Test on Windows
flutter test --platform windows

# Build for Windows
flutter build windows --release
```

## Version Information

The EXE contains the following metadata:
- **File Version:** 1.0.0.1
- **Product Version:** 1.0.0.1
- **Company Name:** UAV Path Planning Team
- **Product Name:** UAV Path Planning
- **File Description:** UAV Path Planning Desktop Application for Windows
- **Copyright:** Copyright (C) 2026 UAV Path Planning Team. All rights reserved.

## Support and Maintenance

### Updating the Application
1. Build new version using `flutter build windows --release`
2. Replace the Release folder contents
3. Test thoroughly before production deployment
4. Update version numbers in pubspec.yaml and Runner.rc

### Backup and Recovery
- Keep a backup of the Release folder
- Store configuration separately from application files
- Document any custom configurations

## Technical Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs for error details
3. Verify system requirements are met
4. Contact the development team with:
   - Windows version
   - Error messages
   - Steps to reproduce
   - Application logs

## Development Notes

### Building from Source

Prerequisites:
- Flutter SDK 3.41.9 or compatible version
- Visual Studio 2022 with C++ desktop development
- Windows 10/11 SDK

Build commands:
```bash
cd uav-mobile-app
flutter pub get
flutter build windows --release
```

### Adding Windows-Specific Features

The application includes platform detection in [main.dart](file:///d:/Developer/workplace/py/iteam/trae/uav-mobile-app/lib/main.dart):
- Platform-specific initialization
- Windows desktop indicators
- Error handling for Windows-specific issues

### Modifying Window Configuration

Window settings are in [windows/runner/main.cpp](file:///d:/Developer/workplace/py/iteam/trae/uav-mobile-app/windows/runner/main.cpp):
- Window title
- Default window size (1280x720)
- Window position (10, 10)

## License

This application is part of the UAV Path Planning System.
See the main project license for details.

## Changelog

### Version 1.0.0 (June 1, 2026)
- Initial Windows desktop release
- Full Flutter desktop support
- Windows 10/11 compatibility
- Error handling and logging
- Secure credential storage
- Network connectivity monitoring
- Material Design 3 UI
