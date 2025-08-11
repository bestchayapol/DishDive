import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/pages/Auth/login.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/widgets/add_image.dart';
import 'package:dishdive/Utils/color_use.dart';

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
  final TextEditingController emailController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final TextEditingController usernameController = TextEditingController();
  final TextEditingController fnameController = TextEditingController();
  final TextEditingController lnameController = TextEditingController();
  final TextEditingController phoneNumController = TextEditingController();
  final TextEditingController confirmPwController = TextEditingController();

  Future<void> signUp() async {
    // Validate the form fields
    if (fnameController.text.isEmpty ||
        passwordController.text.isEmpty ||
        confirmPwController.text.isEmpty ||
        usernameController.text.isEmpty) {
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

    // Send the POST request to the registration endpoint
    final dio = Dio();
    var payload = FormData.fromMap({
      "password": passwordController.text,
      "firstname": fnameController.text,
      "lastname": lnameController.text,
      'file': await MultipartFile.fromFile(
        _selectedImage!.path,
        filename: _selectedImage!.path.split('/').last,
      ),
    });

    try {
      final response = await dio.post(
        'http://10.0.2.2:5428/Register',
        data: payload,
        options: Options(headers: {'Content-Type': 'application/json'}),
      );
      if (response.statusCode == 201) {
        // Registration successful
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration successful')),
        );
        // Clear the form fields
        fnameController.clear();
        lnameController.clear();
        passwordController.clear();
        confirmPwController.clear();

        //navigate to LoginPage()
        Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const LoginPage()),
        );
      } else {
        // Registration failed
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${response.statusCode}')),
        );
      }
    } catch (e) {
      // Network error or other exception
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error: Failed to connect to server')),
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
            // Curved header with back button and title
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
                              fontSize: 40,
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

            // First name
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "First name",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  MyTextField(
                    hintText: 'Your first name',
                    obscureText: false,
                    controller: fnameController,
                    border: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),

            // Last name
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    "Last name",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 6),
                  MyTextField(
                    hintText: 'Your last name',
                    obscureText: false,
                    controller: lnameController,
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
              child: AddImage(
                onImageSelected: (image) {
                  setState(() {
                    _selectedImage = image;
                  });
                },
                textfill: 'Add profile picture +',
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
                fontSize: 32,
                borderRadius: 10,
              ),
            ),
            const SizedBox(height: 20),
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
