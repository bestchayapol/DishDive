import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class MyButton extends StatelessWidget {
  final String text;
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
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width ?? double.infinity,
        height: height,
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 4,
              offset: const Offset(0, 2),
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
            ),
          ),
        ),
      ),
    );
  }
}
