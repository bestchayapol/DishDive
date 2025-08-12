import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class SettingsDropdown extends StatefulWidget {
  final String title;
  final Widget? child;

  const SettingsDropdown({super.key, required this.title, this.child});

  @override
  State<SettingsDropdown> createState() => _SettingsDropdownState();
}

class _SettingsDropdownState extends State<SettingsDropdown> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Yellow bar (category header)
        GestureDetector(
          onTap: () {
            setState(() {
              _expanded = !_expanded;
            });
          },
          child: Container(
            decoration: BoxDecoration(
              color: colorUse.accent,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.08),
                  blurRadius: 2,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    widget.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 22,
                      color: Colors.black,
                    ),
                  ),
                ),
                Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                  color: Colors.black,
                ),
              ],
            ),
          ),
        ),
        // Cream rectangle (expandable content)
        AnimatedCrossFade(
          duration: const Duration(milliseconds: 100),
          crossFadeState: _expanded
              ? CrossFadeState.showFirst
              : CrossFadeState.showSecond,
          firstChild: Container(
            width: double.infinity,
            decoration: BoxDecoration(color: colorUse.secondaryColor),
            padding: const EdgeInsets.all(20),
            child:
                widget.child ??
                const SizedBox(height: 60), // Placeholder for now
          ),
          secondChild: const SizedBox.shrink(),
        ),
        const SizedBox(height: 18),
      ],
    );
  }
}
