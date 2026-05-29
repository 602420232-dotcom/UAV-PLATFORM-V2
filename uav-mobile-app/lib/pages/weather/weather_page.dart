import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:fl_chart/fl_chart.dart';

import '../../config/app_config.dart';
import '../../services/data_source_service.dart';

class WeatherPage extends ConsumerStatefulWidget {
  const WeatherPage({super.key});

  @override
  ConsumerState<WeatherPage> createState() => _WeatherPageState();
}

class _WeatherPageState extends ConsumerState<WeatherPage> {
  DateTime _selectedTime = DateTime.now();
  String _selectedHeight = '100m';
  bool _isLoading = false;
  String? _error;

  double _windSpeed = 0;
  double _windDirection = 0;
  double _temperature = 0;
  double _humidity = 0;
  double _turbulence = 0;
  double _visibility = 0;
  bool _hasData = false;

  @override
  void initState() {
    super.initState();
    _loadWeatherData();
  }

  Future<void> _loadWeatherData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final dsService = DataSourceService();
      final result = await dsService.getDataStatus();

      setState(() {
        _isLoading = false;
        _hasData = true;

        // Parse wind data
        final wind = result['wind'] as Map<String, dynamic>?;
        _windSpeed = (wind?['speed'] as num?)?.toDouble() ?? 0;
        _windDirection = (wind?['direction'] as num?)?.toDouble() ?? 0;

        // Parse weather data
        final weather = result['weather'] as Map<String, dynamic>?;
        _temperature = (weather?['temperature'] as num?)?.toDouble() ?? 0;
        _humidity = (weather?['humidity'] as num?)?.toDouble() ?? 0;
        _turbulence = (weather?['turbulence'] as num?)?.toDouble() ?? 0;
        _visibility = (weather?['visibility'] as num?)?.toDouble() ?? 0;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = e.toString();
      });
    }
  }

  String get _riskLevel {
    if (_windSpeed > 15 || _visibility < 1) return '高';
    if (_windSpeed > 10 || _visibility < 3) return '中';
    return '低';
  }

  Color get _riskColor {
    switch (_riskLevel) {
      case '高':
        return AppConfig.errorColor;
      case '中':
        return AppConfig.warningColor;
      default:
        return AppConfig.successColor;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('气象数据'),
        actions: [
          IconButton(
            icon: _isLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _loadWeatherData,
            tooltip: '刷新',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
                      const SizedBox(height: 12),
                      Text('加载失败: $_error', style: const TextStyle(color: Colors.grey), textAlign: TextAlign.center),
                      const SizedBox(height: 12),
                      ElevatedButton(onPressed: _loadWeatherData, child: const Text('重试')),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildTimeSection(context),
                      const SizedBox(height: 16),
                      _buildWeatherGrid(context),
                      const SizedBox(height: 16),
                      _buildMapSection(context),
                      const SizedBox(height: 16),
                      _buildChartSection(context),
                      const SizedBox(height: 16),
                      _buildDetailSection(context),
                    ],
                  ),
                ),
    );
  }

  Widget _buildTimeSection(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: InkWell(
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: _selectedTime,
                    firstDate: DateTime.now().subtract(const Duration(days: 7)),
                    lastDate: DateTime.now().add(const Duration(days: 3)),
                  );
                  if (picked != null) {
                    setState(() => _selectedTime = picked);
                    _loadWeatherData();
                  }
                },
                child: Row(
                  children: [
                    const Icon(Icons.calendar_today, size: 20),
                    const SizedBox(width: 8),
                    Text('${_selectedTime.year}-${_selectedTime.month.toString().padLeft(2, '0')}-${_selectedTime.day.toString().padLeft(2, '0')}'),
                  ],
                ),
              ),
            ),
            DropdownButton<String>(
              value: _selectedHeight,
              items: ['10m', '50m', '100m', '200m', '500m', '1000m']
                  .map((h) => DropdownMenuItem(value: h, child: Text(h)))
                  .toList(),
              onChanged: (v) {
                if (v != null) {
                  setState(() => _selectedHeight = v);
                  _loadWeatherData();
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeatherGrid(BuildContext context) {
    final items = [
      ('风速', _windSpeed.toStringAsFixed(1), 'm/s', Icons.air, AppConfig.infoColor),
      ('风向', _windDirection.toStringAsFixed(0), '°', Icons.navigation, AppConfig.primaryColor),
      ('温度', _temperature.toStringAsFixed(1), '°C', Icons.thermostat, AppConfig.warningColor),
      ('湿度', _humidity.toStringAsFixed(0), '%', Icons.water_drop, AppConfig.primaryColor),
      ('湍流', _turbulence.toStringAsFixed(2), '', Icons.blur_on, Colors.orange),
      ('能见度', _visibility.toStringAsFixed(1), 'km', Icons.visibility, AppConfig.successColor),
    ];

    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 1.2,
      children: items.map((item) {
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(item.$4, color: item.$5, size: 24),
                const SizedBox(height: 4),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(item.$2, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                    if (item.$3.isNotEmpty) ...[
                      const SizedBox(width: 2),
                      Text(item.$3, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ],
                  ],
                ),
                Text(item.$1, style: const TextStyle(color: Colors.grey, fontSize: 11)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildMapSection(BuildContext context) {
    return SizedBox(
      height: 250,
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [
            FlutterMap(
              options: const MapOptions(initialCenter: LatLng(39.9042, 116.4074), initialZoom: 10),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.uav.planning',
                ),
                MarkerLayer(
                  markers: [
                    Marker(
                      point: const LatLng(39.9042, 116.4074),
                      width: 40,
                      height: 40,
                      child: Transform.rotate(
                        angle: _windDirection * 3.14159 / 180,
                        child: Icon(
                          Icons.navigation,
                          color: _windSpeed > 10 ? AppConfig.errorColor : AppConfig.primaryColor,
                          size: 24,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            Positioned(
              top: 8,
              left: 8,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 4)],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('风险等级: '),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(color: _riskColor, borderRadius: BorderRadius.circular(4)),
                      child: Text(_riskLevel, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartSection(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('风速变化趋势 (24h)', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: _hasData
                  ? LineChart(
                      LineChartData(
                        gridData: const FlGridData(show: true),
                        titlesData: const FlTitlesData(
                          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        lineBarsData: [
                          LineChartBarData(
                            spots: [
                              const FlSpot(0, 0),
                              FlSpot(12, _windSpeed),
                              const FlSpot(24, 0),
                            ],
                            isCurved: true,
                            color: AppConfig.primaryColor,
                            barWidth: 2,
                            dotData: const FlDotData(show: false),
                            belowBarData: BarAreaData(
                              show: true,
                              color: const Color.fromARGB(25, 22, 119, 255),
                            ),
                          ),
                        ],
                      ),
                    )
                  : const Center(child: Text('暂无趋势数据', style: TextStyle(color: Colors.grey))),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailSection(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('详细数据', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _detailRow('风速', '${_windSpeed.toStringAsFixed(1)} m/s'),
            _detailRow('风向', '${_windDirection.toStringAsFixed(0)}°'),
            _detailRow('温度', '${_temperature.toStringAsFixed(1)} °C'),
            _detailRow('湿度', '${_humidity.toStringAsFixed(0)}%'),
            _detailRow('湍流', _turbulence.toStringAsFixed(2)),
            _detailRow('能见度', '${_visibility.toStringAsFixed(1)} km'),
            _detailRow('风险等级', _riskLevel),
            _detailRow('高度', _selectedHeight),
          ],
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
