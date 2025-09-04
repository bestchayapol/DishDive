import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class FlavorSetting extends StatelessWidget {
  final List<String> flavors;
  final Set<String> selectedFlavors;
  final void Function(String) onToggle;  // Changed to single parameter
  final bool isBlacklist;

  const FlavorSetting({
    super.key,
    required this.flavors,
    required this.selectedFlavors,
    required this.onToggle,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: flavors.map((flavor) {
        final selected = selectedFlavors.contains(flavor);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6.0),
          child: _FlavorBox(
            label: flavor,
            selected: selected,
            isBlacklist: isBlacklist,
            onTap: () => onToggle(flavor),  // Now matches the signature
          ),
        );
      }).toList(),
    );
  }
}

class _FlavorBox extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isBlacklist;
  final VoidCallback onTap;

  const _FlavorBox({
    required this.label,
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

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 18,
            color: Colors.black,
            fontWeight: FontWeight.w500,
          ),
        ),
        GestureDetector(
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
        ),
      ],
    );
  }
}
