import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/components/my_textfield.dart';
import 'package:dishdive/widgets/add_image.dart';
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
    
    if (token == null || userId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Authentication error. Please login again.')),
      );
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getEditUserProfileByUserIdEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final parsedJson = response.data;
        setState(() {
          _userNameController.text = parsedJson['username'] ?? '';
        });
      } else {
        throw Exception('Failed to load user data');
      }
    } catch (e) {
      print('Error fetching user data: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to load user data')),
      );
    }
  }

  Future<void> updateUserProfile() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    
    if (token == null || userId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Authentication error. Please login again.')),
      );
      return;
    }

    try {
      Dio dio = Dio();
      FormData formData = FormData();
      
      // Add username to form data (backend expects 'user_name')
      formData.fields.add(MapEntry('user_name', _userNameController.text));
      
      // Add image if selected (backend expects 'file')
      if (_selectedImage != null) {
        String fileName = _selectedImage!.path.split('/').last;
        formData.files.add(MapEntry(
          'file',
          await MultipartFile.fromFile(_selectedImage!.path, filename: fileName),
        ));
      }

      final response = await dio.patch(
        ApiConfig.patchEditUserProfileByUserIdEndpoint(userId),
        data: formData,
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile updated successfully')),
        );
        // Navigate back to profile page
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to update profile')),
        );
      }
    } catch (e) {
      print('Error updating profile: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error updating profile. Please try again.')),
      );
    }
  }

  @override
  void dispose() {
    _userNameController.dispose();
    super.dispose();
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
