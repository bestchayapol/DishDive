import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/widgets/list_dishes.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class RestaurantPage extends StatefulWidget {
  const RestaurantPage({super.key});

  @override
  State<RestaurantPage> createState() => _RestaurantPageState();
}

class _RestaurantPageState extends State<RestaurantPage>
    with SingleTickerProviderStateMixin {
  String? img;
  String? firstname;
  String? lastname;
  String? fullname;
  int? userid;

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
      'http://10.0.2.2:5428/GetProfileOfCurrentUserByUserId/$userId',
      options: Options(
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      ),
    );

    if (response.statusCode == 200) {
      final parsedJson = response.data;
      setState(() {
        img = parsedJson['user_pic'];
        firstname = parsedJson['firstname'];
        lastname = parsedJson['lastname'];
        fullname = '$firstname $lastname';
        userid = userId;
      });
    } else {
      throw Exception('Failed to load user data');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: colorUse.backgroundColor,
      body: Column(
        children: [
          // Top bar with back button, restaurant name, and profile icon
          Container(
            color: colorUse.appBarColor,
            padding: const EdgeInsets.only(
              top: 40,
              left: 16,
              right: 16,
              bottom: 18,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Back button
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: Colors.white),
                  onPressed: () => Navigator.pop(context),
                ),
                const SizedBox(width: 8),
                // Restaurant name (centered)
                Expanded(
                  child: Text(
                    "Restaurant Name",
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontFamily: 'InriaSans',
                      fontWeight: FontWeight.bold,
                      fontSize: 32,
                      color: Colors.white,
                    ),
                  ),
                ),
                // Profile icon (right)
                GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => Profile()),
                    );
                  },
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Menu label
          Container(
            width: double.infinity,
            color: colorUse.backgroundColor,
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            child: const Text(
              "Menu",
              style: TextStyle(
                color: Colors.white,
                fontSize: 22,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          // Vertical grid of grey rectangles as placeholders for menu cards
          Expanded(child: ListDishesGrid()),
        ],
      ),
    );
  }
}
