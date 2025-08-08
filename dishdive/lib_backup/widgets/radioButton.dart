import 'package:flutter/material.dart';
import 'package:dishdive/Utils/text_use.dart';

class Radiobutton extends StatefulWidget {
  final String title; // Required title
  final List<String> labels; // List of radio button labels
  final ValueChanged<String>? onChanged; // Callback for selection changes

  const Radiobutton({
    super.key,
    required this.title,
    required this.labels,
    this.onChanged,
  });

  @override
  State<Radiobutton> createState() => _RadiobuttonState();
}

class _RadiobuttonState extends State<Radiobutton> {
  String? _selectedLabel; // Store the currently selected label

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: RegularText(widget.title),
        ),
        Column(
          children: widget.labels.map((label) {
            return RadioListTile<String>(
              title: Text(label),
              value: label,
              groupValue: _selectedLabel,
              onChanged: (String? value) {
                setState(() {
                  _selectedLabel = value;
                });
                widget.onChanged?.call(value!);
              },
            );
          }).toList(),
        ),
      ],
    );
  }
}
