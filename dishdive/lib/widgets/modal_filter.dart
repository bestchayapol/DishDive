import 'package:dishdive/Utils/color_use.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/Pages/Preferences/PreferencesSettings.dart';
import 'package:dishdive/Pages/Preferences/BlacklistSettings.dart';

class FilterModal extends StatelessWidget {
  const FilterModal({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Material(
        color: Colors.transparent,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 320,
              padding: const EdgeInsets.symmetric(vertical: 12),
              decoration: BoxDecoration(
                color: colorUse.accent,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(10),
                  topRight: Radius.circular(10),
                ),
              ),
              child: const Text(
                "Set filter",
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'InriaSans',
                  fontWeight: FontWeight.bold,
                  fontSize: 36,
                  color: Colors.black,
                ),
              ),
            ),
            Container(
              width: 320,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: colorUse.secondaryColor,
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(10),
                  bottomRight: Radius.circular(10),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.12),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 10.0),
                    child: MyButton(
                      text: "Preferences",
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => SetPref()),
                        );
                      },
                      backgroundColor: colorUse.activeButton,
                      textColor: Colors.black,
                      fontSize: 25,
                      borderRadius: 10,
                      width: 205,
                      height: 60,
                      icon: const Icon(
                        Icons.restaurant_menu,
                        color: Colors.black,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  // Blacklist button
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 10.0),
                    child: MyButton(
                      text: "Blacklist",
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => SetBlack()),
                        );
                      },
                      backgroundColor: Colors.black,
                      textColor: colorUse.activeButton,
                      fontSize: 25,
                      borderRadius: 10,
                      width: 205,
                      height: 60,
                      borderColor: colorUse.activeButton,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
