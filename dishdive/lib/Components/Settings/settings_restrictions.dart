import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class RestrictionSetting extends StatelessWidget {
  final List<String> restrictions;
  final Set<String> selectedRestrictions;
  final bool isBlacklist;
  final void Function(String) onToggle;

  const RestrictionSetting({
    super.key,
    required this.restrictions,
    required this.selectedRestrictions,
    required this.onToggle,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: restrictions.map((restriction) {
        final selected = selectedRestrictions.contains(restriction);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6.0),
          child: _RestrictionBox(
            label: restriction,
            selected: selected,
            isBlacklist: isBlacklist,
            onTap: () => onToggle(restriction),
          ),
        );
      }).toList(),
    );
  }
}

class _RestrictionBox extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isBlacklist;
  final VoidCallback onTap;

  const _RestrictionBox({
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
