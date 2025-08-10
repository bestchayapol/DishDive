import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:dishdive/Pages/Auth/LoR.dart';
import 'package:dishdive/Pages/Profile/edit_profile.dart';
import 'package:dishdive/Pages/Profile/eula.dart';
import 'package:dishdive/Utils/color_use.dart';
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
      body: Stack(
        children: [
          // Bottom rectangles (replace spheres)
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Row(
              children: [
                Expanded(
                  child: Container(height: 60, color: colorUse.sentimentColor),
                ),
                Expanded(
                  child: Container(height: 60, color: Colors.amber[200]),
                ),
              ],
            ),
          ),
          SingleChildScrollView(
            child: Column(
              children: [
                // Top section with back, logout, and profile
                Container(
                  color: colorUse.appBarColor,
                  padding: const EdgeInsets.only(
                    top: 40,
                    left: 16,
                    right: 16,
                    bottom: 0,
                  ),
                  child: Stack(
                    children: [
                      // Back button
                      Align(
                        alignment: Alignment.topLeft,
                        child: TextButton.icon(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(
                            Icons.arrow_back,
                            color: Colors.white,
                          ),
                          label: const Text(
                            "Back",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          style: TextButton.styleFrom(
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                      // Logout button
                      Align(
                        alignment: Alignment.topRight,
                        child: TextButton(
                          onPressed: logout,
                          child: const Text(
                            "Log out",
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                      // Profile picture (centered)
                      Column(
                        children: [
                          const SizedBox(height: 40),
                          Center(
                            child: Stack(
                              alignment: Alignment.bottomRight,
                              children: [
                                FutureBuilder<Map<String, dynamic>>(
                                  future: _userData,
                                  builder: (context, snapshot) {
                                    String? profilePic =
                                        snapshot.data?['user_pic'];
                                    return CircleAvatar(
                                      radius: 54,
                                      backgroundColor: Colors.white,
                                      backgroundImage:
                                          profilePic != null &&
                                              profilePic.isNotEmpty
                                          ? NetworkImage(profilePic)
                                          : null,
                                    );
                                  },
                                ),
                                Positioned(
                                  bottom: 0,
                                  right: 0,
                                  child: GestureDetector(
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) =>
                                              const EditProfile(),
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
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
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
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    );
                  },
                ),
                const SizedBox(height: 24),
                // Preferences button
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32.0),
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pushNamed(context, '/preferences');
                    },
                    icon: const Icon(
                      Icons.restaurant_menu,
                      color: Colors.black,
                    ),
                    label: const Text(
                      "Preferences",
                      style: TextStyle(
                        color: Colors.black,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: colorUse.activeButton,
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      elevation: 0,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Blacklist button
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 32.0),
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pushNamed(context, '/blacklist');
                    },
                    child: const Text(
                      "Blacklist",
                      style: TextStyle(
                        color: colorUse.activeButton,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: colorUse.activeButton, width: 2),
                      minimumSize: const Size.fromHeight(48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 80),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void logout() {
    Provider.of<TokenProvider>(context, listen: false).setToken("", 0);
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const LoginOrRegister()),
    );
  }
}
