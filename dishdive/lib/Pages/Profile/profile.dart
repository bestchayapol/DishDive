import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/Pages/Auth/LoR.dart';
import 'package:dishdive/Pages/Profile/edit_profile.dart';
import 'package:dishdive/Pages/Profile/eula.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/widgets/BackgroundCircle.dart';
import 'package:provider/provider.dart';
import 'package:dishdive/provider/token_provider.dart';

class Profile extends StatefulWidget {
  const Profile({Key? key});

  @override
  State<Profile> createState() => _ProfileState();
}

class _ProfileState extends State<Profile> {
  Future<Map<String, dynamic>>? _userData;

  @override
  void initState() {
    super.initState();
    _userData = fetchUserData();
  }

  void logout() {
    Provider.of<TokenProvider>(context, listen: false).setToken("", 0);
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const LoginOrRegister()),
    );
  }

  Future<Map<String, dynamic>> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;

    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetProfileOfCurrentUserByUserId/$userId',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      return response.data;
    } else {
      throw Exception('Failed to load user data');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Top section: curved background + profile picture
            buildTopSection(),
            const SizedBox(height: 16),
            // Username (centered)
            FutureBuilder<Map<String, dynamic>>(
              future: _userData,
              builder: (context, snapshot) {
                String username = snapshot.data?['username'] ?? "Username";
                return Text(
                  username,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                );
              },
            ),
            const SizedBox(height: 90),
            // Preferences button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 80.0,
                vertical: 10.0,
              ),
              child: MyButton(
                text: "Preferences",
                onTap: () {
                  Navigator.pushNamed(context, '/preferences');
                },
                backgroundColor: colorUse.activeButton,
                textColor: Colors.black,
                fontSize: 32,
                borderRadius: 10,
                icon: const Icon(Icons.restaurant_menu, color: Colors.black),
              ),
            ),
            const SizedBox(height: 20),
            // Blacklist button
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 80.0,
                vertical: 10.0,
              ),
              child: MyButton(
                text: "Blacklist",
                onTap: () {
                  Navigator.pushNamed(context, '/blacklist');
                },
                backgroundColor: Colors.black,
                textColor: colorUse.activeButton,
                fontSize: 32,
                borderRadius: 10,
                borderColor: colorUse.activeButton,
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: SizedBox(
        height: 80,
        child: Column(
          children: [
            Expanded(child: Container(color: colorUse.accent)),
            Expanded(child: Container(color: colorUse.activeButton)),
          ],
        ),
      ),
    );
  }

  Widget buildTopSection() {
    final double coverHeight = 200;
    final double profileHeight = 108;

    final double top = coverHeight - profileHeight / 2;
    final double bottom = profileHeight / 2;

    return Stack(
      clipBehavior: Clip.none,
      alignment: Alignment.center,
      children: [
        // Curved background
        Container(
          margin: EdgeInsets.only(bottom: bottom),
          child: BackgroundCircle(
            height: coverHeight,
            color: colorUse.appBarColor,
          ),
        ),
        // Profile picture (centered, overlapping)
        Positioned(
          top: top,
          child: FutureBuilder<Map<String, dynamic>>(
            future: _userData,
            builder: (context, snapshot) {
              String? profilePic = snapshot.data?['user_pic'];
              return Stack(
                alignment: Alignment.bottomRight,
                children: [
                  CircleAvatar(
                    radius: profileHeight / 2,
                    backgroundColor: Colors.white,
                    backgroundImage: profilePic != null && profilePic.isNotEmpty
                        ? NetworkImage(profilePic)
                        : null,
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: GestureDetector(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const EditProfile(),
                          ),
                        );
                      },
                      child: Container(
                        decoration: BoxDecoration(
                          color: colorUse.activeButton,
                          shape: BoxShape.circle,
                        ),
                        padding: const EdgeInsets.all(6),
                        child: const Icon(
                          Icons.edit,
                          color: Colors.white,
                          size: 20,
                        ),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
        // Back and Logout buttons (top left and right)
        Positioned(
          left: 0,
          top: 40,
          child: TextButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            label: const Text(
              "Back",
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            style: TextButton.styleFrom(foregroundColor: Colors.white),
          ),
        ),
        Positioned(
          right: 0,
          top: 40,
          child: TextButton(
            onPressed: logout,
            child: const Text(
              "Log out",
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
