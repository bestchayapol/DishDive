import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class CuisineSetting extends StatelessWidget {
  final List<String> cuisines;
  final Set<String> selectedCuisines;
  final bool isBlacklist;
  final void Function(String) onToggle;

  const CuisineSetting({
    super.key,
    required this.cuisines,
    required this.selectedCuisines,
    required this.onToggle,
    this.isBlacklist = false,
  });

  @override
  Widget build(BuildContext context) {
    // 2 columns
    final left = <Widget>[];
    final right = <Widget>[];
    for (int i = 0; i < cuisines.length; i++) {
      final cuisine = cuisines[i];
      final selected = selectedCuisines.contains(cuisine);
      left.add(
        _CuisineBox(
          label: cuisine,
          selected: selected,
          isBlacklist: isBlacklist,
          onTap: () => onToggle(cuisine),
        ),
      );
      if (++i < cuisines.length) {
        final cuisine2 = cuisines[i];
        final selected2 = selectedCuisines.contains(cuisine2);
        right.add(
          _CuisineBox(
            label: cuisine2,
            selected: selected2,
            isBlacklist: isBlacklist,
            onTap: () => onToggle(cuisine2),
          ),
        );
      }
    }

    // Pair up left and right columns
    List<Widget> rows = [];
    for (int i = 0; i < left.length; i++) {
      rows.add(
        Row(
          children: [
            Expanded(child: left[i]),
            const SizedBox(width: 16),
            Expanded(child: i < right.length ? right[i] : const SizedBox()),
          ],
        ),
      );
      rows.add(const SizedBox(height: 12));
    }

    return Column(children: rows);
  }
}

class _CuisineBox extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isBlacklist;
  final VoidCallback onTap;

  const _CuisineBox({
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
