import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';
import 'package:dishdive/Utils/api_config.dart';
import 'package:dishdive/Components/my_button.dart';
import 'package:dishdive/Components/Cards/card_details.dart';
import 'package:dishdive/Pages/Restaurant/ReviewPage.dart';
import 'package:dishdive/Pages/Profile/profile.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:dishdive/services/restaurant_service.dart';
import 'package:dishdive/models/dish_detail.dart';
import 'package:provider/provider.dart';

class DishPage extends StatefulWidget {
  final int dishId;
  final String dishName;
  final int restaurantId;

  const DishPage({
    super.key,
    required this.dishId,
    required this.dishName,
    required this.restaurantId,
  });

  @override
  State<DishPage> createState() => _DishPageState();
}

class _DishPageState extends State<DishPage>
    with SingleTickerProviderStateMixin {
  final RestaurantService _restaurantService = RestaurantService();
  DishDetail? _dishDetail;
  bool _isLoading = true;
  String? _error;
  String? profileImageUrl;
  String? username;
  int? userid;

  @override
  void initState() {
    super.initState();
    fetchUserData();
    _fetchDishDetail();
  }

  Future<void> _fetchDishDetail() async {
    final tokenProvider = Provider.of<TokenProvider>(context, listen: false);
    final token = tokenProvider.token;
    final userId = tokenProvider.userId;

    if (token == null || userId == null) {
      setState(() {
        _error = 'User not authenticated';
        _isLoading = false;
      });
      return;
    }

    try {
      final dishDetail = await _restaurantService.getDishDetail(
        widget.dishId,
        userId,
        token,
      );

      setState(() {
        _dishDetail = dishDetail;
        _isLoading = false;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleFavorite() async {
    if (_dishDetail == null) return;

    final tokenProvider = Provider.of<TokenProvider>(context, listen: false);
    final token = tokenProvider.token;
    final userId = tokenProvider.userId;

    if (token == null || userId == null) return;

    bool success;
    if (_dishDetail!.isFavorite) {
      success = await _restaurantService.removeFavorite(
        userId,
        widget.dishId,
        token,
      );
    } else {
      success = await _restaurantService.addFavorite(
        userId,
        widget.dishId,
        token,
      );
    }

    if (success) {
      setState(() {
        _dishDetail = DishDetail(
          dishId: _dishDetail!.dishId,
          dishName: _dishDetail!.dishName,
          imageLink: _dishDetail!.imageLink,
          sentimentScore: _dishDetail!.sentimentScore,
          positiveReviews: _dishDetail!.positiveReviews,
          totalReviews: _dishDetail!.totalReviews,
          cuisine: _dishDetail!.cuisine,
          prominentFlavor: _dishDetail!.prominentFlavor,
          topKeywords: _dishDetail!.topKeywords,
          isFavorite: !_dishDetail!.isFavorite,
        );
      });
    } else {
      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _dishDetail!.isFavorite
                ? 'Failed to remove favorite'
                : 'Failed to add favorite',
          ),
          backgroundColor: Colors.red,
        ),
      );
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
          // Content area
          Expanded(child: _buildContent()),
          // Write Review button (only when restaurantId is valid)
          if (widget.restaurantId > 0) ...[
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
                    MaterialPageRoute(
                      builder: (_) => ReviewPage(
                        dishId: widget.dishId,
                        resId: widget.restaurantId,
                      ),
                    ),
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
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Failed to load dish details',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _error!,
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _fetchDishDetail,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_dishDetail == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.restaurant_menu, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Dish not found',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: CardDetails(
        dishId: _dishDetail!.dishId,
        imagePath: _dishDetail!.imageLink ?? "assets/Logo.png",
        dishName: _dishDetail!.dishName,
        cuisine: _dishDetail!.cuisineDisplay,
        taste: _dishDetail!.tasteDisplay,
        ratingPercent: _dishDetail!.ratingPercent,
        positiveReviews: _dishDetail!.positiveReviews,
        totalReviews: _dishDetail!.totalReviews,
        keywords: _dishDetail!.allKeywords,
        isFavorite: _dishDetail!.isFavorite,
        onFavoriteToggle: _toggleFavorite,
      ),
    );
  }
}
