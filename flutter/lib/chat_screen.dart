import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'dart:convert';
import 'dart:async';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<String> messages = [];
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;
  String? userId; // ✅ 로그인된 사용자 ID

  final String lmStudioUrl = 'http://192.168.137.200:5412/v1/chat/completions';
  final String flaskUrl = 'http://121.139.20.242:15180/chat';

  @override
  void initState() {
    super.initState();
    _loadUserId(); // 비동기 함수 따로 호출
  }

  Future<void> _loadUserId() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      userId = prefs.getString('user_id');
    });
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> sendMessageToLMStudio(String userInput) async {
    if (userId == null) {
      setState(() {
        messages.add("❌ 사용자 정보를 불러오지 못했습니다.");
      });
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // 1. 사용자 메시지 Flask에 저장
      await http.post(
        Uri.parse(flaskUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "user_id": userId,
          "content": userInput,
          "type": "user",
        }),
      );

      // 2. LM Studio에 메시지 전송
      final requestBody = {
        "model": "meta-llama-3.1-8b-instruct",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": userInput},
        ],
        "temperature": 0.7,
        "stream": false,
      };

      final response = await http
          .post(
            Uri.parse(lmStudioUrl),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(requestBody),
          )
          .timeout(Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final reply = data['choices'][0]['message']['content'];

        // 3. 봇 응답 저장
        await http.post(
          Uri.parse(flaskUrl),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "user_id": userId,
            "content": reply,
            "type": "bot",
          }),
        );

        setState(() {
          messages.add("🤖 $reply");
        });
      } else {
        setState(() {
          messages.add("⚠️ 서버 오류: ${response.statusCode}");
        });
      }
    } on TimeoutException {
      setState(() {
        messages.add("⚠️ 응답 시간 초과");
      });
    } catch (e) {
      setState(() {
        messages.add("❌ 오류 발생: $e");
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty || _isLoading) return;

    setState(() {
      messages.add("👤 $text");
      _controller.clear();
    });

    _scrollToBottom();
    sendMessageToLMStudio(text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E7),
      appBar: AppBar(
        title: Text('TTOTTO AI 채팅'),
        backgroundColor: Colors.amber,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: EdgeInsets.all(8),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final message = messages[index];
                final isUser = message.startsWith('👤');
                return Align(
                  alignment:
                      isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.amber[100] : Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 2,
                          offset: Offset(0, 1),
                        ),
                      ],
                    ),
                    child: Text(message, style: TextStyle(fontSize: 16)),
                  ),
                );
              },
            ),
          ),
          if (_isLoading)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 4,
                  offset: Offset(0, -1),
                ),
              ],
            ),
            padding: EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    enabled: !_isLoading,
                    decoration: InputDecoration(
                      hintText: _isLoading ? '응답 대기 중...' : '메시지를 입력하세요',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLoading ? null : _sendMessage,
                  child: Text('전송'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.amber,
                    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
