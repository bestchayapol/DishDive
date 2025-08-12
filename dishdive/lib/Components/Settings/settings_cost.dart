import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class CostSetting extends StatelessWidget {
  final List<String> costs;
  final Set<String> selectedCosts;
  final bool isBlacklist;
  final void Function(String) onToggle;

  const CostSetting({
    super.key,
    required this.costs,
    required this.selectedCosts,
    required this.onToggle,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: costs.map((cost) {
        final selected = selectedCosts.contains(cost);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6.0),
          child: _CostBox(
            label: cost,
            selected: selected,
            isBlacklist: isBlacklist,
            onTap: () => onToggle(cost),
          ),
        );
      }).toList(),
    );
  }
}

class _CostBox extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isBlacklist;
  final VoidCallback onTap;

  const _CostBox({
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
