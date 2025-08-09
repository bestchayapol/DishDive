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
  const SignUpPage({super.key, required this.onTap});

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
        emailController.text.isEmpty ||
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match')),
      );
      return;
    }

    // Send the POST request to the registration endpoint
    final dio = Dio();
    var payload = FormData.fromMap({
      "username": usernameController.text,
      "password": passwordController.text,
      "email": emailController.text,
      "firstname": fnameController.text,
      "lastname": lnameController.text,
      "phonenum": phoneNumController.text,
      'file': await MultipartFile.fromFile(
        _selectedImage!.path,
        filename: _selectedImage!.path.split('/').last,
      ),
    });

    try {
      final response = await dio.post(
        'http://10.0.2.2:5428/Register',
        data: payload,
        options: Options(
          headers: {
            'Content-Type': 'application/json',
          },
        ),
      );
      if (response.statusCode == 201) {
        // Registration successful
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration successful')),
        );
        // Clear the form fields
        usernameController.clear();
        fnameController.clear();
        lnameController.clear();
        phoneNumController.clear();
        emailController.clear();
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
      backgroundColor: colorUse.backgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Curved header with back button and title
            Stack(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
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
                //app name0
                const Text(
                  "Register",
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w600),
                ),

                const SizedBox(height: 50),

                //username textfield
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "username",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
                    ),
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Input your username',
                      obscureText: false,
                      controller: usernameController,
                      border: true,
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      "first name",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
                    ],
                  ),
                    ),
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Input your first name',
                      obscureText: false,
                      controller: fnameController,
                      border: true,
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      "last name",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
                    ),
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Input your last name',
                      obscureText: false,
                      controller: lnameController,
                      border: true,
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                //email textfield
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "email",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
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
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Input email address',
                      obscureText: false,
                      controller: emailController,
                      border: true,
                    ),
                  ],
                ),

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
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "phone number",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
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
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Input Your phone number',
                      obscureText: false,
                      controller: phoneNumController,
                      border: true,
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                //password textfield
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "password",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
                    ),
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Enter Password',
                      obscureText: true,
                      controller: passwordController,
                      iconData: Icons.remove_red_eye_outlined,
                      border: true,
                      onIconPressed: () {
                        // Callback function to be called when the icon is pressed
                      },
                    ),
                  ],
                ),

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
                const SizedBox(height: 20),

                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "confirm password",
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: Color.fromARGB(255, 0, 0, 0),
                      ),
                    ),
                    const SizedBox(height: 5),
                    MyTextField(
                      hintText: 'Confirm Password',
                      obscureText: true,
                      controller: confirmPwController,
                      iconData: Icons.remove_red_eye_outlined,
                      border: true,
                      onIconPressed: () {
                        // Callback function to be called when the icon is pressed
                      },
                    ),
                  ],
                ),

            // Add profile picture
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: AddImage(
                onImageSelected: (image) {
                  if (image != null) {
                    setState(() {
                      _selectedImage = image;
                    });
                  }
                },
                textfill: 'Add profile picture +',
              ),
            ),
            const SizedBox(height: 20),
                const SizedBox(height: 35),

            // Sign up button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 90.0,
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
                Padding(
                  padding: const EdgeInsets.only(top: 20.0),
                  child: AddImage(
                      onImageSelected: (image) {
                        if (image != null) {
                          setState(() {
                            _selectedImage = image;
                          });
                        }
                      },
                      textfill: 'Please add profile picture'),
                ),

                //sign in button
                MyButton(
                  text: "Sign Up",
                  width: 400,
                  height: 50,
                  onTap: signUp,
                ),

                const SizedBox(height: 30),

                //horizontal line
                Container(
                  width: double.infinity,
                  height: 1,
                  color: Colors.grey.shade400,
                  child: const DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          Color.fromARGB(255, 205, 204, 204),
                          Color.fromARGB(255, 205, 204, 204)
                        ],
                        stops: [0.5, 0.5],
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ),
                    ),
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

                const SizedBox(height: 25),
                //register here
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      "Already have an account? ",
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    GestureDetector(
                      onTap: widget.onTap,
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
        ),
      ),
    );
  }
}
