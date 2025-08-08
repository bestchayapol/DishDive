import 'package:flutter/material.dart';
import 'package:dishdive/Utils/text_use.dart';


class ButtonAtBottom extends StatelessWidget {
  final VoidCallback onPressed;
  final Color? color;
  final String text;

  const ButtonAtBottom(
      {super.key, required this.onPressed, required this.text, this.color});

  @override
  Widget build(BuildContext context) {
    return 
          Column(
            children: [
              LayoutBuilder(
                builder: (context, constraints) {
                  return Container(
                    alignment: Alignment.bottomCenter,
                    child: ElevatedButton(
                      onPressed: onPressed,
                      style: ElevatedButton.styleFrom(
                        fixedSize: Size(constraints.maxWidth * 0.8, 50),
                        backgroundColor: color,
                      ),
                      child: RegularTextButton(text),
                    ),
                  );
                },
              ),
              const SizedBox(height: 30,)
            ],
          );
       
  }
}

