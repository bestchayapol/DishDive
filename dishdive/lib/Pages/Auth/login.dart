import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/pages/home.dart';
// import 'package:dishdive/provider/token_provider.dart';
// import 'package:provider/provider.dart';
import 'package:dishdive/Utils/color_use.dart';
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
  final Dio dio = Dio();

  @override
void dispose() {
  usernameController.dispose();
  passwordController.dispose();
  super.dispose();
}

  void _navigateToFirstHomePage(String token) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const Home()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.primaryColor,
      body: SingleChildScrollView(
<<<<<<< Updated upstream
        padding: const EdgeInsets.only(top: 90),
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(25.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 25),
                //app name0
                const Text(
                  "Sign In",
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
                ),

                const SizedBox(height: 50),

                //email textfield
                MyTextField(
                  hintText: 'Enter Username',
                  obscureText: false,
                  controller: usernameController,
                ),

                const SizedBox(height: 20),

                //password textfield
                MyTextField(
                  hintText: 'Enter Password',
                  obscureText: true,
                  controller: passwordController,
                  iconData: Icons.remove_red_eye_outlined,
                  onIconPressed: () {
                    // Callback function to be called when the icon is pressed
                  },
                ),

                const SizedBox(height: 25),

                //forgot password
                // Row(
                //   mainAxisAlignment: MainAxisAlignment.end,
                //   children: [
                //     Text(
                //       "Forgot Password",
                //       style: TextStyle(
                //         color: Theme.of(context).colorScheme.secondary,
                //       ),
                //     )
                //   ],
                // ),

                const SizedBox(height: 25),

                //sign in button
                MyButton(
                  text: "Sign In",
                  width: 400,
                  height: 58,
                  onTap: () {
                              String fakeToken = "test123";
                              _navigateToFirstHomePage(fakeToken);
                            },
                ),

                const SizedBox(height: 40),

                //register here
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      "Don't have an account? ",
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
=======
        child: Column(
          children: [
            // Curved header with logo and app name
            Container(
              width: MediaQuery.of(context).size.width,
              padding: const EdgeInsets.only(top: 80, bottom: 40),
              decoration: BoxDecoration(color: colorUse.appBarColor),
              child: Column(
                children: [
                  Text(
                    'DishDive',
                    style: TextStyle(
                      fontSize: 64,
                      fontWeight: FontWeight.bold,
                      color: colorUse.activeButton,
>>>>>>> Stashed changes
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 40),
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
            const SizedBox(height: 36),
            // Username/email textfield
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: MyTextField(
                hintText: 'Email or User Name',
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
                horizontal: 90.0,
                vertical: 10.0,
              ),
              child: MyButton(
                text: "Sign in",
                onTap: () {
                  String fakeToken = "test123";
                  _navigateToFirstHomePage(fakeToken);
                },
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
