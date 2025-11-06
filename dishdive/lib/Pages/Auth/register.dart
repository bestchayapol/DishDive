import 'dart:io';
import 'package:flutter/material.dart';
import 'package:dishdive/pages/Auth/login.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/widgets/add_image.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/services/auth_service.dart';

// CHANGES:
// - Removed unused controllers and fields
// - Unified layout to match login page structure (header, title, fields, button, prompt)
// - Used MyTextField for all fields
// - Added back button in header
// - Adjusted field order and labels to match the provided image
// - Kept image picker and sign up logic

class SignUpPage extends StatefulWidget {
  final void Function()? onTap;

  const SignUpPage({super.key, this.onTap});

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  File? _selectedImage;
  //text controllers
  final TextEditingController passwordController = TextEditingController();
  final TextEditingController usernameController = TextEditingController();
  final TextEditingController confirmPwController = TextEditingController();
  final AuthService _authService = AuthService();

  Future<void> signUp() async {
    // Validate the form fields
    if (usernameController.text.isEmpty ||
        passwordController.text.isEmpty ||
        confirmPwController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill in all fields')),
      );
      return;
    }

    if (passwordController.text != confirmPwController.text) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Passwords do not match')));
      return;
    }

    if (_selectedImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a profile picture')),
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
      final result = await _authService.register(
        usernameController.text,
        passwordController.text,
        _selectedImage!,
      );

      // Hide loading indicator
      Navigator.of(context).pop();

      if (result['success']) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(result['message'])));

        // Clear the form fields
        usernameController.clear();
        passwordController.clear();
        confirmPwController.clear();
        setState(() {
          _selectedImage = null;
        });

        // Navigate to LoginPage
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const LoginPage()),
        );
      } else {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(result['message'])));
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
            Stack(
              children: [
                Container(
                  width: MediaQuery.of(context).size.width,
                  padding: const EdgeInsets.only(bottom: 15),
                  decoration: BoxDecoration(color: colorUse.appBarColor),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Centered Register text
                      Padding(
                        padding: EdgeInsets.only(
                          top: 60,
                        ), // Adjust this value as needed
                        child: Align(
                          alignment: Alignment.center,
                          child: Text(
                            "Register",
                            style: TextStyle(
                              fontFamily: 'InriaSans',
                              fontSize: 32,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                      // Back button on the left
                      Align(
                        alignment: Alignment.centerLeft,
                        child: IconButton(
                          icon: const Icon(
                            Icons.arrow_back,
                            color: Colors.white,
                          ),
                          iconSize: 32,
                          padding: EdgeInsets.zero,
                          onPressed: () {
                            Navigator.of(
                              context,
                            ).popUntil((route) => route.isFirst);
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Username
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Username",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  MyTextField(
                    hintText: 'Your username',
                    obscureText: false,
                    controller: usernameController,
                    border: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Password
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Password",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  MyTextField(
                    hintText: 'Password',
                    obscureText: true,
                    controller: passwordController,
                    border: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Confirm password
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Confirm password",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  MyTextField(
                    hintText: 'Confirm password',
                    obscureText: true,
                    controller: confirmPwController,
                    border: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 25),

            // Add profile picture
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Profile Picture",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Center(
                    child: AddImage(
                      onImageSelected: (image) {
                        setState(() {
                          _selectedImage = image;
                        });
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Profile picture selected!'),
                            duration: Duration(seconds: 2),
                          ),
                        );
                      },
                      textfill: _selectedImage != null
                          ? 'Change picture'
                          : 'Add profile picture +',
                    ),
                  ),
                  if (_selectedImage != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8.0),
                      child: Center(
                        child: Text(
                          '✓ Image selected',
                          style: TextStyle(
                            color: colorUse.activeButton,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            // Sign up button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 80.0,
                vertical: 10.0,
              ),
              child: MyButton(
                text: "Sign up",
                onTap: signUp,
                backgroundColor: colorUse.activeButton,
                textColor: Colors.white,
                fontSize: 25,
                borderRadius: 10,
                width: 145,
                height: 60,
              ),
            ),
            const SizedBox(height: 14),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  "Already have an account? ",
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w500,
                    color: Colors.white,
                  ),
                ),
                GestureDetector(
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
                  child: const Text(
                    "Sign in",
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: colorUse.activeButton,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
