import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Components/my_button.dart';
import 'package:dishdive/Components/Cards/card_details.dart';
import 'package:dishdive/Pages/Restaurant/ReviewPage.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class DishPage extends StatefulWidget {
  final int dishId;
  final String dishName;

  const DishPage({
    super.key,
    required this.dishId,
    required this.dishName,
  });

  @override
  State<DishPage> createState() => _DishPageState();
}

class _DishPageState extends State<DishPage>
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
                const Spacer(),
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
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: CardDetails(
                imagePath: "assets/Logo.png",
                dishName: "Fried rice",
                cuisine: "Thai",
                taste: "Salty",
                ratingPercent: 92,
                positiveReviews: 2355,
                totalReviews: 2560,
                keywords: [
                  {"label": "Salty", "count": 111, "type": "taste"},
                  {"label": "Budget", "count": 36, "type": "cost"},
                  {"label": "Perfect", "count": 166, "type": "general"},
                  {"label": "Big portion", "count": 129, "type": "general"},
                  {"label": "Good rice", "count": 82, "type": "general"},
                  {"label": "Not enough meat", "count": 63, "type": "general"},
                  {"label": "Hangover food", "count": 57, "type": "general"},
                ],
              ),
            ),
          ),
          const SizedBox(height: 15),
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 80.0,
              vertical: 10.0,
            ),
            child: MyButton(
              text: "Write Review",
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ReviewPage()),
                );
              },
              backgroundColor: colorUse.activeButton,
              textColor: Colors.white,
              fontSize: 32,
              borderRadius: 10,
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
