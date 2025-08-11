import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class BackgroundCircle extends StatelessWidget {
  final double height;
  final Color? color;

  const BackgroundCircle({Key? key, this.height = 200, this.color})
    : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        height: height,
        width: double.infinity,
        decoration: BoxDecoration(
          color: color ?? colorUse.appBarColor,
          borderRadius: const BorderRadius.only(
            bottomLeft: Radius.elliptical(220, 60),
            bottomRight: Radius.elliptical(220, 60),
          ),
        ),
      ),
    );
  }
}
