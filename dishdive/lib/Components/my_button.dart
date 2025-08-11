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
  final Widget? icon; // <-- Add this
  final Color? borderColor; // <-- Add this

  const MyButton({
    Key? key,
    required this.text,
    this.onTap,
    this.width,
    this.height = 70,
    this.backgroundColor = colorUse.activeButton,
    this.textColor = Colors.white,
    this.fontSize = 18,
    this.borderRadius = 8,
    this.icon,
    this.borderColor,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width ?? double.infinity,
      height: height,
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          foregroundColor: textColor,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(borderRadius),
            side: borderColor != null
                ? BorderSide(color: borderColor!, width: 2)
                : BorderSide.none,
          ),
          elevation: 0,
        ),
        child: icon != null
            ? Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  icon!,
                  const SizedBox(width: 8),
                  Text(
                    text,
                    style: TextStyle(
                      color: textColor,
                      fontSize: fontSize,
                      fontWeight: FontWeight.normal,
                    ),
                  ),
                ],
              )
            : Text(
                text,
                style: TextStyle(
                  color: textColor,
                  fontSize: fontSize,
                  fontWeight: FontWeight.normal,
                ),
              ),
      ),
    );
  }
}
