import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class MyTextField extends StatefulWidget {
  final String hintText;
  final bool obscureText;
  final TextEditingController controller;
  final IconData? iconData;
  final VoidCallback? onIconPressed;
  final bool? border;

  const MyTextField({
    super.key,
    required this.hintText,
    required this.obscureText,
    required this.controller,
    this.iconData,
    this.onIconPressed,
    this.border,
  });

  @override
  State<MyTextField> createState() => _MyTextFieldState();
}

class _MyTextFieldState extends State<MyTextField> {
  late bool obscureText;
  late IconData iconData;

  @override
  void initState() {
    super.initState();
    obscureText = widget.obscureText;
    iconData = obscureText
        ? Icons.remove_red_eye_outlined
        : Icons.remove_red_eye;
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: widget.controller,
      decoration: InputDecoration(
        contentPadding: const EdgeInsets.symmetric(
          vertical: 11,
          horizontal: 20,
        ),
        hintText: widget.hintText,
        prefixIcon: widget.iconData != null
            ? Icon(widget.iconData, color: Colors.black87)
            : null,
        suffixIcon: widget.obscureText
            ? IconButton(
                icon: Icon(iconData),
                onPressed: () {
                  setState(() {
                    obscureText = !obscureText;
                    iconData = obscureText
                        ? Icons.remove_red_eye_outlined
                        : Icons.remove_red_eye;
                  });
                  if (widget.onIconPressed != null) {
                    widget.onIconPressed!();
                  }
                },
              )
            : null,
        filled: true,
        fillColor: colorUse.secondaryColor,
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(
            color: widget.border ?? false
                ? colorUse.accent
                : Colors.transparent,
            width: 3,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(
            color: widget.border ?? false
                ? colorUse.accent
                : Colors.transparent,
            width: 3,
          ),
        ),
      ),
      obscureText: obscureText,
      style: const TextStyle(fontSize: 18),
    );
  }
}
