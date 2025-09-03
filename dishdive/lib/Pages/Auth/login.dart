import 'package:flutter/material.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/Pages/home.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/services/auth_service.dart';
import 'package:provider/provider.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/widgets/BackgroundCircle.dart';
import 'package:dishdive/pages/Auth/register.dart';

class LoginPage extends StatefulWidget {
  final void Function()? onTap;

  const LoginPage({super.key, this.onTap});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController usernameController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final AuthService _authService = AuthService();

  @override
  void dispose() {
    usernameController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  void _navigateToFirstHomePage(String token, int userId) {
    // Store token and user ID in provider
    Provider.of<TokenProvider>(context, listen: false).setToken(token, userId);
    
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const Home()),
    );
  }

  Future<void> login() async {
    // Validate the form fields
    if (usernameController.text.isEmpty || passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill in all fields')),
      );
      return;
    }

    // Show loading indicator
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final result = await _authService.login(
        usernameController.text,
        passwordController.text,
      );

      // Hide loading indicator
      Navigator.of(context).pop();

      if (result['success']) {
        final responseData = result['data'];
        final String token = responseData['token'] ?? '';
        final int userId = responseData['user_id'] ?? 0;

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'])),
        );

        // Clear the form fields
        usernameController.clear();
        passwordController.clear();

        // Navigate to home page with token and user ID
        _navigateToFirstHomePage(token, userId);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'])),
        );
      }
    } catch (e) {
      // Hide loading indicator
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('An unexpected error occurred')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.primaryColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Curved header with app name
            Stack(
              children: [
                BackgroundCircle(height: 220), // Adjust height as needed
                Container(
                  width: MediaQuery.of(context).size.width,
                  padding: const EdgeInsets.only(top: 80, bottom: 40),
                  child: Column(
                    children: [
                      Text(
                        'DishDive',
                        style: TextStyle(
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
            const SizedBox(height: 60),
            // Login title
            const Text(
              "Login",
              style: TextStyle(
                fontFamily: 'InriaSans',
                fontSize: 48,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 60),
            // Username/email textfield
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: MyTextField(
                hintText: 'Username',
                obscureText: false,
                controller: usernameController,
                iconData: Icons.person_outline,
                border: true, // or false if you want no border
              ),
            ),
            const SizedBox(height: 35),
            // Password textfield
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: MyTextField(
                hintText: 'Password',
                obscureText: true,
                controller: passwordController,
                iconData: Icons.lock_outline,
                border: true,
              ),
            ),
            const SizedBox(height: 36),
            // Sign in button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 80.0,
                vertical: 10.0,
              ),
              child: MyButton(
                text: "Sign in",
                onTap: login,
                backgroundColor: colorUse.activeButton,
                textColor: Colors.white,
                fontSize: 32,
                borderRadius: 10,
              ),
            ),
            const SizedBox(height: 40),
            // Register prompt
            Padding(
              padding: const EdgeInsets.only(bottom: 24.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    "Don’t have an account? ",
                    style: TextStyle(
                      fontFamily: 'InriaSans',
                      fontSize: 16,
                      color: Colors.white,
                    ),
                  ),
                  GestureDetector(
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
                    child: Text(
                      "Register",
                      style: TextStyle(
                        fontFamily: 'InriaSans',
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: colorUse.activeButton,
                      ),
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
