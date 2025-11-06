import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/components/my_button.dart';
import 'package:dishdive/Components/Cards/card_reviews.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/services/restaurant_service.dart';
import 'package:dishdive/models/review_models.dart';
import 'package:provider/provider.dart';

class ReviewPage extends StatefulWidget {
  final int dishId;
  final int resId;

  const ReviewPage({super.key, required this.dishId, required this.resId});

  @override
  State<ReviewPage> createState() => _ReviewPageState();
}

class _ReviewPageState extends State<ReviewPage>
    with SingleTickerProviderStateMixin {
  String? username;
  String? profileImageUrl;
  int? userid;

  // Dish data
  DishReviewPageResponse? dishData;
  bool isLoadingDish = true;
  String? dishError;

  final RestaurantService _restaurantService = RestaurantService();

  @override
  void initState() {
    super.initState();
    fetchUserData();
    fetchDishData();
  }

  Future<void> fetchDishData() async {
    try {
      final token = Provider.of<TokenProvider>(context, listen: false).token;
      if (token == null) {
        setState(() {
          dishError = 'No authentication token found';
          isLoadingDish = false;
        });
        return;
      }

      final data = await _restaurantService.getDishReviewPage(
        widget.dishId,
        token,
      );
      setState(() {
        dishData = data;
        isLoadingDish = false;
      });
    } catch (e) {
      setState(() {
        dishError = e.toString();
        isLoadingDish = false;
      });
    }
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

  final TextEditingController _reviewController = TextEditingController();

  Future<void> submitReview() async {
    if (_reviewController.text.trim().isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Please write a review.")));
      return;
    }

    if (userid == null || dishData == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Missing user or dish data.")),
      );
      return;
    }

    try {
      final token = Provider.of<TokenProvider>(context, listen: false).token;
      if (token == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Authentication token not found.")),
        );
        return;
      }

      final request = SubmitReviewRequest(
        dishId: widget.dishId,
        resId: widget.resId,
        userId: userid!,
        reviewText: _reviewController.text.trim(),
      );

      final response = await _restaurantService.submitReview(request, token);

      if (response.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Review submitted successfully!")),
        );
        _reviewController.clear();
        Navigator.pop(context); // Go back to dish detail page
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to submit review.")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error submitting review: $e")));
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
                Expanded(
                  child: Text(
                    "Review",
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontFamily: 'InriaSans',
                      fontWeight: FontWeight.bold,
                      fontSize: 24,
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
                      color: Colors.grey, // Placeholder color
                    ),
                    child:
                        profileImageUrl != null && profileImageUrl!.isNotEmpty
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
                              loadingBuilder:
                                  (context, child, loadingProgress) {
                                    if (loadingProgress == null) return child;
                                    return const Center(
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        valueColor:
                                            AlwaysStoppedAnimation<Color>(
                                              Colors.white,
                                            ),
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
          Expanded(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Dish card
                    if (isLoadingDish)
                      const Center(child: CircularProgressIndicator())
                    else if (dishError != null)
                      Center(
                        child: Text(
                          'Error loading dish: $dishError',
                          style: const TextStyle(color: Colors.red),
                        ),
                      )
                    else if (dishData != null)
                      CardReviews(
                        reviewController: _reviewController,
                        dishData: dishData!,
                      )
                    else
                      const Center(child: Text('No dish data available')),
                    const SizedBox(height: 240),
                  ],
                ),
              ),
            ),
          ),
          // Submit button (match DishPage spacing/style)
          const SizedBox(height: 15),
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 80.0,
              vertical: 10.0,
            ),
            child: MyButton(
              text: "Submit",
              onTap: submitReview,
              backgroundColor: colorUse.activeButton,
              textColor: Colors.white,
              fontSize: 25,
              borderRadius: 10,
              width: 145,
              height: 60,
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
