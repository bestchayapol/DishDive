import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class TextStyles {
  static TextStyle headingStyle() {
    return const TextStyle(
      color: Color.fromARGB(255, 0, 0, 0),
      fontSize: 22.0,
      fontWeight: FontWeight.bold,
    );
  }

  static TextStyle regularTextStyleBold() {
    return const TextStyle(
      fontSize: 16.0,
      fontWeight: FontWeight.bold,
    );
  }

  static TextStyle regularTextStyle() {
    return const TextStyle(
      fontSize: 16.0,
    );
  }

  static TextStyle regularTextStyleButton() {
    return const TextStyle(
        fontSize: 16.0,
        color: colorUse.textColorButton,
        fontWeight: FontWeight.bold);
  }

  static TextStyle cardTitleStyle() {
    return const TextStyle(
      fontSize: 18.0,
      fontWeight: FontWeight.w800,
    );
  }

  static TextStyle cardSubtitleStyle() {
    return const TextStyle(
      fontSize: 14.0,
      fontWeight: FontWeight.w600,
    );
  }
}

class Heading extends StatelessWidget {
  final String text;

  const Heading(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(text, style: TextStyles.headingStyle());
  }
}

class RegularTextBold extends StatelessWidget {
  final String text;

  const RegularTextBold(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(text, style: TextStyles.regularTextStyleBold());
  }
}

class RegularText extends StatelessWidget {
  final String text;

  const RegularText(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(text, style: TextStyles.regularTextStyle());
  }
}

class RegularTextButton extends StatelessWidget {
  final String text;

  const RegularTextButton(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Text(text, style: TextStyles.regularTextStyleButton());
  }
}
