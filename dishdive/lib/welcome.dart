import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Auth/login.dart';
import 'package:dishdive/Pages/Auth/register.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, TargetPlatform, kIsWeb;
import 'package:dishdive/widgets/BackgroundCircle.dart';

class Welcome extends StatelessWidget {
  final VoidCallback onFinished;

  const Welcome({super.key, required this.onFinished});

  @override
  Widget build(BuildContext context) {
    String _resolveBaseUrl() {
      const envBase = String.fromEnvironment('BACKEND_BASE');
      if (envBase.isNotEmpty) return envBase;
      if (kIsWeb) {
        // On web dev, the origin is the Flutter dev server (e.g., :46920).
        // Default to the Go backend port instead; override with BACKEND_BASE when needed.
        return 'http://localhost:8080';
      }
      if (defaultTargetPlatform == TargetPlatform.android) {
        // Android emulator maps host loopback to 10.0.2.2
        return 'http://10.0.2.2:8080';
      }
      // iOS simulator / desktop
      return 'http://localhost:8080';
    }

    return Scaffold(
      backgroundColor: colorUse.primaryColor,
      body: Column(
        children: [
          // Curved header section with logo and app name
          Stack(
            children: [
              BackgroundCircle(height: 360), // Adjust height as needed
              Container(
                width: MediaQuery.of(context).size.width,
                padding: const EdgeInsets.only(top: 70, bottom: 40),
                child: Column(
                  children: [
                    SizedBox(
                      width: 170,
                      height: 170,
                      child: Image.asset("assets/Logo.png"),
                    ),
                    const SizedBox(height: 10),
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
            ],
          ),
          const SizedBox(height: 70),
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
              horizontal: 80.0,
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
              },
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
              horizontal: 80.0,
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
              backgroundColor: colorUse.secondaryColor,
              textColor: colorUse.activeButton,
              fontSize: 32,
              borderRadius: 10,
            ),
          ),
          const SizedBox(height: 10),
          // ...existing code...
        ],
      ),
    );
  }
}
