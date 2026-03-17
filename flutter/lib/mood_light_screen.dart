import 'package:flutter/material.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

class MoodLightScreen extends StatefulWidget {
  @override
  _MoodLightScreenState createState() => _MoodLightScreenState();
}

class _MoodLightScreenState extends State<MoodLightScreen> {
  Color color = Colors.amber;
  double brightness = 1.0;
  bool isOn = true;

  Color get finalColor => color.withOpacity(brightness);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFF8E7),
      appBar: AppBar(
        title: Text('무드등 제어'),
        backgroundColor: Colors.yellow[700],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            Icon(
              Icons.lightbulb,
              size: 100,
              color: isOn ? finalColor : Colors.grey,
            ),
            SizedBox(height: 16),
            SwitchListTile(
              title: Text('무드등 ${isOn ? "켜짐" : "꺼짐"}'),
              value: isOn,
              onChanged: (val) => setState(() => isOn = val),
            ),
            Text("밝기: ${(brightness * 100).round()}%"),
            Slider(
              value: brightness,
              onChanged: (val) => setState(() => brightness = val),
              min: 0.0,
              max: 1.0,
              divisions: 10,
            ),
            SizedBox(height: 16),

            SizedBox(height: 16),
            ColorPicker(
              pickerColor: color,
              onColorChanged: (c) => setState(() => color = c),
              pickerAreaHeightPercent: 0.8,
              enableAlpha: false,
              displayThumbColor: false,
              showLabel: false,
              paletteType: PaletteType.hsv,
            ),
          ],
        ),
      ),
    );
  }
}
