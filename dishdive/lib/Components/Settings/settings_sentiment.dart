import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class SentimentSetting extends StatelessWidget {
  final int value;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;
  final bool isBlacklist;

  const SentimentSetting({
    super.key,
    required this.value,
    required this.onIncrement,
    required this.onDecrement,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    // Colors and text depend on page type
    final boxColor = isBlacklist ? Colors.black : colorUse.sentimentColor;
    final textColor = isBlacklist ? Colors.white : Colors.black;
    final labelText = isBlacklist ? "Less than" : "At least";
    final suffixText = isBlacklist ? "% positive" : "% positive or more";

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              labelText,
              style: const TextStyle(fontSize: 20, color: Colors.black),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              decoration: BoxDecoration(
                color: boxColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                value.toString(),
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: textColor,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              suffixText,
              style: const TextStyle(fontSize: 20, color: Colors.black),
            ),
          ],
        ),
        const SizedBox(height: 18),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: onDecrement,
              style: ElevatedButton.styleFrom(
                backgroundColor: colorUse.activeButton,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                minimumSize: const Size(56, 40),
                elevation: 0,
              ),
              child: const Text(
                "-",
                style: TextStyle(fontSize: 28, color: Colors.white),
              ),
            ),
            const SizedBox(width: 24),
            ElevatedButton(
              onPressed: onIncrement,
              style: ElevatedButton.styleFrom(
                backgroundColor: colorUse.activeButton,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                minimumSize: const Size(56, 40),
                elevation: 0,
              ),
              child: const Text(
                "+",
                style: TextStyle(fontSize: 28, color: Colors.white),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
