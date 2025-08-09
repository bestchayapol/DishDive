import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class MyButton extends StatelessWidget {
  final String text;
  final double width;
  final double height;
  final void Function()? onTap;
  final double? width;
  final double? height;
  final Color backgroundColor;
  final Color textColor;
  final double fontSize;
  final double borderRadius;

  const MyButton({
    super.key,
    required this.text,
    required this.onTap,
    this.width,
    this.height = 60,
    this.backgroundColor = colorUse.activeButton,
    this.textColor = Colors.white,
    this.fontSize = 32,
    this.borderRadius = 10,
    required this.width,
    required this.height,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width ?? double.infinity,
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(borderRadius),
          color: colorUse.activeButton,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 4,
              offset: const Offset(0, 2),
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Center(
          child: Text(
            text,
            style: TextStyle(
              fontWeight: FontWeight.normal,
              fontSize: fontSize,
              color: textColor,
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}
