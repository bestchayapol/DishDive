import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/text_use.dart';

class ButtonForPopUp extends StatelessWidget {
  final VoidCallback onPressed;
  final String text;

  const ButtonForPopUp(
      {super.key, required this.onPressed, required this.text});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: colorUse.activeButton,
        fixedSize: const Size(400, 40), // Set a fixed size to the button
      ),
      child: RegularTextButton(text),
    );
  }
}
