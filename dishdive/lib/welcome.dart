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
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            const SizedBox(
              height: 50,
            ),
            Image.asset(
              "assets/Logo.jpg",
              width: 400,
              height: 400,
            ),
            const SizedBox(
              height: 10,
            ),
            const Text('Welcome to Needful!',
                style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: colorUse.accent)),
            const SizedBox(
              height: 35,
            ),
            ElevatedButton(
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
                fixedSize: const Size(200, 50),
                elevation: 5,
                backgroundColor: colorUse.activeButton
              ),
              child: const Text(
                "Login",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(
              height: 15,
            ),
            ElevatedButton(
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
            ),
          ],
        ),
      ),
    );
  }
}
