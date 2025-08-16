import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
// Commented out for static data example
// import 'package:dio/dio.dart';
// import 'package:provider/provider.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/widgets/add_image.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class EditProfile extends StatefulWidget {
  const EditProfile({super.key});

  @override
  State<EditProfile> createState() => _EditProfileState();
}

class _EditProfileState extends State<EditProfile> {
  File? _selectedImage;
  final _userNameController = TextEditingController();

  @override
  void initState() {
    super.initState();
    fetchUserData();
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    Dio dio = Dio();
    final response = await dio.get(
      'http://10.0.2.2:5428/GetEditUserProfileByUserId/$userId',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data; // Directly get the parsed data
      setState(() {
        _userNameController.text = parsedJson['username'] ?? '';
      });
    } else {
      throw Exception('Failed to load user data');
    }
  }

  Future<void> updateUserProfile() async {
    Dio dio = Dio();
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    final data = {"username": _userNameController.text};

    final response = await dio.patch(
      'http://10.0.2.2:5428/PatchEditUserProfileByUserId/$userId',
      data: json.encode(data),
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json', // Adjust content type as needed
        },
      ),
    );

    if (response.statusCode == 200) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated successfully')),
      );
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Failed to update profile')));
    }

    // Static response for testing
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Profile updated successfully (static data)'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      appBar: AppBar(
        backgroundColor: colorUse.appBarColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Edit Profile",
          style: TextStyle(
            fontFamily: 'InriaSans',
            fontWeight: FontWeight.bold,
            fontSize: 32,
            color: Colors.white,
          ),
        ),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
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
                    controller: _userNameController,
                    border: true,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),

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
                text: "Save edit",
                onTap: updateUserProfile,
                backgroundColor: colorUse.activeButton,
                textColor: Colors.white,
                fontSize: 32,
                borderRadius: 10,
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
