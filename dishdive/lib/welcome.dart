import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Auth/login.dart';
import 'package:dishdive/Pages/Auth/register.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/components/my_button.dart';

class Welcome extends StatelessWidget {
  final VoidCallback onFinished;

  const Welcome({super.key, required this.onFinished});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.primaryColor,
      body: Column(
        children: [
          // Black header section with logo and app name
          Container(
            width: MediaQuery.of(context).size.width,
            padding: const EdgeInsets.only(top: 90, bottom: 40),
            decoration: BoxDecoration(color: colorUse.appBarColor),
            child: Column(
              children: [
                Image.asset("assets/Logo.png"),
                const SizedBox(height: 16),
                Text(
                  'DishDive',
                  style: TextStyle(
                    fontSize: 64,
                    fontWeight: FontWeight.bold,
                    color: colorUse.accent)),
            const SizedBox(
              height: 35,
            ),
              ],
            ),
          ),
          const SizedBox(height: 65),
          // Subtitle
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32.0),
            child: Text(
              'See reviews of\nyour favorite dish',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 36,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 55),
          // Login Button
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 90.0,
              vertical: 10.0,
            ),
            child: MyButton(
              text: "Login",
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => LoginPage(
                      onTap: () {
                        Navigator.pop(context);
                      },
                    ),
                  ),
                );
              }

              backgroundColor: colorUse.activeButton,
              textColor: Colors.white,
              fontSize: 32,
              borderRadius: 10,
            ),
            const SizedBox(
              height: 15,
            ),
            ElevatedButton(
              onPressed: () {

              backgroundColor: colorUse.activeButton,
              textColor: Colors.white,
              fontSize: 32,
              borderRadius: 10,
            ),
          ),
          const SizedBox(height: 20),
          // Register Button
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 90.0,
              vertical: 10.0,
            ),
            child: MyButton(
              text: "Register",
              onTap: () {

                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => SignUpPage(
                      onTap: () {
                        Navigator.pop(context);
                      },
                    ),
                  ),
                );
              },

              style: ElevatedButton.styleFrom(
                fixedSize: const Size(200, 50),
                elevation: 5,
                backgroundColor: colorUse.accent,
              ),
              child: const Text(
                "Register",
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.black54),
              ),

              backgroundColor: colorUse.secondaryColor,
              textColor: colorUse.activeButton,
              fontSize: 32,
              borderRadius: 10,

            ),
          ],
        ),

              backgroundColor: colorUse.secondaryColor,
              textColor: colorUse.activeButton,
              fontSize: 32,
              borderRadius: 10,
            ),
          ),
        ],

      ),
    );
  }
}
