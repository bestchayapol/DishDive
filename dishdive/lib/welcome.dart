import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Auth/login.dart';
import 'package:dishdive/Pages/Auth/register.dart';
import 'package:dishdive/Utils/color_use.dart';

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
            padding: const EdgeInsets.only(top: 60, bottom: 40),
            decoration: BoxDecoration(color: colorUse.appBarColor),
            child: Column(
              children: [
                Image.asset("assets/Logo.png"),
                const SizedBox(height: 16),
                Text(
                  'DishDive',
                  style: TextStyle(
                    fontFamily: 'InriaSans',
                    fontSize: 64,
                    fontWeight: FontWeight.bold,
                    color: colorUse.activeButton,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 60),
          // Subtitle
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32.0),
            child: Text(
              'See reviews of\nyour favorite dish',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 36,
                color: Colors.white,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          const Spacer(),
          // Login Button
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40.0),
            child: ElevatedButton(
              onPressed: () {
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
              },
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(55),
                backgroundColor: colorUse.activeButton,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(15),
                ),
              ),
              child: const Text(
                "Login",
                style: TextStyle(
                  fontFamily: 'InriaSans',
                  color: Colors.white,
                  fontSize: 32,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Register Button
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40.0),
            child: ElevatedButton(
              onPressed: () {
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
                minimumSize: const Size.fromHeight(55),
                backgroundColor: colorUse.secondaryColor,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(15),
                ),
              ),
              child: Text(
                "Register",
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w600,
                  color: colorUse.activeButton,
                ),
              ),
            ),
          ),
          const SizedBox(height: 50),
        ],
      ),
    );
  }
}
