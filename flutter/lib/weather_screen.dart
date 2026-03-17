import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class WeatherScreen extends StatefulWidget {
  @override
  _WeatherScreenState createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  String _weather = '날씨 정보를 불러오는 중...';
  String _temperature = '';
  String _city = '자동 감지 중...';
  bool _isLoading = true;

  //한글 → 영어 도시명 매핑 딕셔너리
  final Map<String, String> cityKoToEn = {
    '서울': 'Seoul',
    '안양': 'Anyang',
    '군포': 'Gunpo',
    '부산': 'Busan',
    '인천': 'Incheon',
    '대전': 'Daejeon',
    '대구': 'Daegu',
    '광주': 'Gwangju',
    '수원': 'Suwon',
    // 필요 시 추가
  };

  @override
  void initState() {
    super.initState();
    _determinePositionAndFetchWeather();
  }

  Future<void> _determinePositionAndFetchWeather() async {
    setState(() {
      _isLoading = true;
    });

    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('위치 권한이 거부되었습니다.');
        }
      }

      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      List<Placemark> placemarks = await placemarkFromCoordinates(
        position.latitude,
        position.longitude,
      );

      String cityName = placemarks[0].locality ?? 'Seoul';
      setState(() {
        _city = cityName;
      });

      _fetchWeather(cityName);
    } catch (e) {
      setState(() {
        _city = '안양'; // 기본값
      });
      _fetchWeather('Anyang'); // 영어로 API 요청
    }
  }

  Future<void> _fetchWeather(String city) async {
    final apiKey = dotenv.env['OPENWEATHER_API_KEY'] ?? '';
    final url =
        'https://api.openweathermap.org/data/2.5/weather?q=$city&appid=$apiKey&units=metric&lang=kr';

    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _weather = data['weather'][0]['description'];
          _temperature = '${data['main']['temp'].round()}°C';
          _isLoading = false;
        });
      } else {
        setState(() {
          _weather = '날씨 정보를 가져오는데 실패했습니다.';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _weather = '네트워크 오류가 발생했습니다.';
        _isLoading = false;
      });
    }
  }

  IconData _getWeatherIcon() {
    final w = _weather.toLowerCase();
    if (w.contains('맑')) return Icons.wb_sunny;
    if (w.contains('구름')) return Icons.cloud;
    if (w.contains('비')) return Icons.beach_access;
    if (w.contains('눈')) return Icons.ac_unit;
    return Icons.wb_cloudy;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFFFF8E7),
      appBar: AppBar(title: Text('오늘 날씨'), backgroundColor: Colors.orange),
      body: Center(
        child:
            _isLoading
                ? CircularProgressIndicator()
                : Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(_getWeatherIcon(), size: 80, color: Colors.orange),
                    SizedBox(height: 16),
                    Text(
                      '$_city\n$_weather\n$_temperature',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _determinePositionAndFetchWeather,
                      child: Text('새로고침'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange,
                      ),
                    ),
                  ],
                ),
      ),
    );
  }
}
