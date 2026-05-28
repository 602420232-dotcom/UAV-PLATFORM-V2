import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../config/app_config.dart';
import '../../providers/app_providers.dart';

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
              onTap: () {},
            ),
            ListTile(
              leading: const Icon(Icons.bluetooth),
              title: const Text('边缘计算节点'),
              subtitle: const Text('http://localhost:8000'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {},
            ),
          ]),
          _buildSection(context, '系统', [
            SwitchListTile(
              secondary: const Icon(Icons.map),
              title: const Text('离线地图缓存'),
              subtitle: const Text('缓存地图数据以节省流量'),
              value: true,
              onChanged: (val) {},
            ),
            SwitchListTile(
              secondary: const Icon(Icons.notifications),
              title: const Text('推送通知'),
              subtitle: const Text('接收任务状态和气象预警通知'),
              value: true,
              onChanged: (val) {},
            ),
            SwitchListTile(
              secondary: const Icon(Icons.dark_mode),
              title: const Text('深色模式'),
              subtitle: const Text('适合夜间飞行作业'),
              value: false,
              onChanged: (val) {},
            ),
          ]),
          _buildSection(context, '数据', [
            ListTile(
              leading: const Icon(Icons.cached),
              title: const Text('清除缓存'),
              subtitle: const Text('清除本地缓存数据'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('缓存已清除')),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.storage),
              title: const Text('数据使用量'),
              subtitle: const Text('15.2 MB'),
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
              label: const Text(
                '退出登录',
                style: TextStyle(color: AppConfig.errorColor),
              ),
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

  Widget _buildSection(
    BuildContext context,
    String title,
    List<Widget> children,
  ) {
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
