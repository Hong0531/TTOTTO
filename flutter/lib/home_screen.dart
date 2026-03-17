import 'package:flutter/material.dart';
import 'chat_screen.dart';
import 'weather_screen.dart';
import 'mood_light_screen.dart';
import 'login_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E7),
      appBar: AppBar(
        title: const Text('TTOTTO'),
        backgroundColor: Colors.amber,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              showDialog(
                context: context,
                builder:
                    (context) => AlertDialog(
                      title: const Text('로그아웃'),
                      content: const Text('정말 로그아웃 하시겠습니까?'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('취소'),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pushAndRemoveUntil(
                              context,
                              MaterialPageRoute(builder: (_) => LoginScreen()),
                              (route) => false,
                            );
                          },
                          child: const Text('로그아웃'),
                        ),
                      ],
                    ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 32),
            Image.asset('assets/logo.png', height: 80),
            const Text(
              'TTOTTO',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 32),
            MenuButton(
              title: '실시간 채팅',
              icon: Icons.chat,
              color: Colors.lightBlue,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => ChatScreen()),
                );
              },
            ),
            MenuButton(
              title: '오늘 날씨 보기',
              icon: Icons.cloud,
              color: Colors.orange,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => WeatherScreen()),
                );
              },
            ),
            MenuButton(
              title: '무드등 제어하기',
              icon: Icons.lightbulb,
              color: Colors.yellow.shade700,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => MoodLightScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class MenuButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const MenuButton({
    super.key,
    required this.title,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            children: [
              Icon(icon, size: 32, color: color),
              const SizedBox(width: 16),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
