import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/widgets/list_dishes.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class RestaurantPage extends StatefulWidget {
  final int restaurantId;
  final String restaurantName;

  const RestaurantPage({
    super.key,
    required this.restaurantId,
    required this.restaurantName,
  });

  @override
  State<RestaurantPage> createState() => _RestaurantPageState();
}

class _RestaurantPageState extends State<RestaurantPage>
    with SingleTickerProviderStateMixin {
  String? profileImageUrl;
  String? username;
  int? userid;

  @override
  void initState() {
    super.initState();
    fetchUserData();
  }

  Future<void> fetchUserData() async {
    final token = Provider.of<TokenProvider>(context, listen: false).token;
    final userId = Provider.of<TokenProvider>(context, listen: false).userId;
    
    if (token == null || userId == null) {
      return;
    }

    try {
      Dio dio = Dio();
      final response = await dio.get(
        ApiConfig.getProfileOfCurrentUserByUserIdEndpoint(userId),
        options: Options(headers: ApiConfig.authHeaders(token)),
      );

      if (response.statusCode == 200) {
        final parsedJson = response.data;
        setState(() {
          profileImageUrl = parsedJson['image_link'];
          username = parsedJson['username'];
          userid = userId;
        });
      }
    } catch (e) {
      print('Error fetching user data: $e');
      // Handle error silently for now
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
                    widget.restaurantName,
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
                    child: profileImageUrl != null && profileImageUrl!.isNotEmpty
                        ? ClipOval(
                            child: Image.network(
                              profileImageUrl!,
                              width: 48,
                              height: 48,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return const Icon(
                                  Icons.person,
                                  color: Colors.white,
                                  size: 24,
                                );
                              },
                              loadingBuilder: (context, child, loadingProgress) {
                                if (loadingProgress == null) return child;
                                return const Center(
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                );
                              },
                            ),
                          )
                        : const Icon(
                            Icons.person,
                            color: Colors.white,
                            size: 24,
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
          Expanded(
            child: ListDishesGrid(
              restaurantId: widget.restaurantId,
              restaurantName: widget.restaurantName,
            ),
          ),
        ],
      ),
    );
  }
}
