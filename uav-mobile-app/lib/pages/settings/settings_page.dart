import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/app_config.dart';
import '../../providers/app_providers.dart';
import '../../services/offline_manager.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  bool _darkMode = false;
  bool _offlineCache = true;
  bool _pushNotifications = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        children: [
          _buildSection(context, '服务器配置', [
            ListTile(
              leading: const Icon(Icons.dns),
              title: const Text('API 服务器地址'),
              subtitle: Text(AppConfig.apiBaseUrl),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _showServerConfigDialog(context),
            ),
            ListTile(
              leading: const Icon(Icons.bluetooth),
              title: const Text('边缘计算节点'),
              subtitle: Text(AppConfig.apiEndpoints['edge'] ?? 'http://localhost:8000'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
          _buildSection(context, '系统', [
            SwitchListTile(
              secondary: const Icon(Icons.map),
              title: const Text('离线地图缓存'),
              subtitle: const Text('缓存地图数据以节省流量'),
              value: _offlineCache,
              onChanged: (val) => setState(() => _offlineCache = val),
            ),
            SwitchListTile(
              secondary: const Icon(Icons.notifications),
              title: const Text('推送通知'),
              subtitle: const Text('接收任务状态和气象预警通知'),
              value: _pushNotifications,
              onChanged: (val) => setState(() => _pushNotifications = val),
            ),
            SwitchListTile(
              secondary: Icon(_darkMode ? Icons.dark_mode : Icons.light_mode),
              title: const Text('深色模式'),
              subtitle: const Text('适合夜间飞行作业'),
              value: _darkMode,
              onChanged: (val) {
                setState(() => _darkMode = val);
                // Apply theme change globally
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('深色模式已${val ? '开启' : '关闭'}（重启生效）')),
                );
              },
            ),
          ]),
          _buildSection(context, '数据', [
            ListTile(
              leading: const Icon(Icons.cached),
              title: const Text('清除缓存'),
              subtitle: const Text('清除本地缓存数据'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () async {
                try {
                  final manager = OfflineManager();
                  await manager.clearCache();
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('缓存已清除'), backgroundColor: AppConfig.successColor),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('清除失败: $e'), backgroundColor: AppConfig.errorColor),
                    );
                  }
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.storage),
              title: const Text('数据使用量'),
              subtitle: const Text('需联网获取'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
          _buildSection(context, '关于', [
            const ListTile(
              leading: Icon(Icons.info),
              title: Text('版本'),
              subtitle: Text('v${AppConfig.appVersion}'),
            ),
            ListTile(
              leading: const Icon(Icons.description),
              title: const Text('开源许可'),
              subtitle: const Text('MIT License'),
              onTap: () {},
            ),
          ]),
          Padding(
            padding: const EdgeInsets.all(16),
            child: OutlinedButton.icon(
              onPressed: () async {
                final authService = ref.read(authServiceProvider);
                await authService.logout();
                ref.read(currentUserProvider.notifier).state = null;
                ref.read(isLoggedInProvider.notifier).state = false;
                if (context.mounted) {
                  context.go('/login');
                }
              },
              icon: const Icon(Icons.logout, color: AppConfig.errorColor),
              label: const Text('退出登录', style: TextStyle(color: AppConfig.errorColor)),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppConfig.errorColor),
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showServerConfigDialog(BuildContext context) {
    final controller = TextEditingController(text: AppConfig.apiBaseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('API 服务器地址'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'http://localhost:8088'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          FilledButton(
            onPressed: () {
              if (controller.text.isNotEmpty && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('服务器地址已更新（重启后生效）')),
                );
              }
              Navigator.pop(ctx);
            },
            child: const Text('保存'),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: AppConfig.primaryColor,
                  fontWeight: FontWeight.bold,
                ),
          ),
        ),
        ...children,
        const Divider(),
      ],
    );
  }
}
