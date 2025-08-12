import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class FlavorSetting extends StatelessWidget {
  final List<String> flavors;
  final Set<String> zeroToMedium;
  final Set<String> mediumToHigh;
  final void Function(String, bool) onToggle;
  final bool isBlacklist;

  const FlavorSetting({
    super.key,
    required this.flavors,
    required this.zeroToMedium,
    required this.mediumToHigh,
    required this.onToggle,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    List<Widget> rows = [
      Row(
        children: const [
          SizedBox(width: 80),
          Expanded(
            child: Center(
              child: Text(
                "Zero to medium",
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
              ),
            ),
          ),
          Expanded(
            child: Center(
              child: Text(
                "Medium to high",
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
    ];

    for (final flavor in flavors) {
      rows.add(
        Row(
          children: [
            SizedBox(
              width: 80,
              child: Text(
                flavor,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Expanded(
              child: Center(
                child: _FlavorBox(
                  selected: zeroToMedium.contains(flavor),
                  isBlacklist: isBlacklist,
                  onTap: () => onToggle(flavor, false),
                ),
              ),
            ),
            Expanded(
              child: Center(
                child: _FlavorBox(
                  selected: mediumToHigh.contains(flavor),
                  isBlacklist: isBlacklist,
                  onTap: () => onToggle(flavor, true),
                ),
              ),
            ),
          ],
        ),
      );
      rows.add(const SizedBox(height: 10));
    }

    return Column(children: rows);
  }
}

class _FlavorBox extends StatelessWidget {
  final bool selected;
  final bool isBlacklist;
  final VoidCallback onTap;

  const _FlavorBox({
    required this.selected,
    required this.isBlacklist,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color boxColor;
    Widget? icon;
    if (selected) {
      if (isBlacklist) {
        boxColor = Colors.black;
        icon = const Icon(Icons.close, color: Colors.white, size: 22);
      } else {
        boxColor = colorUse.sentimentColor;
        icon = const Icon(Icons.check, color: Colors.black, size: 22);
      }
    } else {
      boxColor = Colors.transparent;
      icon = null;
    }

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 28,
        height: 28,
        decoration: BoxDecoration(
          color: boxColor,
          border: Border.all(color: Colors.black, width: 2),
          borderRadius: BorderRadius.circular(6),
        ),
        child: icon,
      ),
    );
  }
}
