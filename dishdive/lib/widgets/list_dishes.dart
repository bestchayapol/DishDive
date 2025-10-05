import 'package:flutter/material.dart';
import 'package:dishdive/Components/Cards/card_menu.dart';
import 'package:dishdive/Pages/Restaurant/DishPage.dart';
import 'package:dishdive/models/restaurant_menu_item.dart';
import 'package:dishdive/services/restaurant_service.dart';
import 'package:dishdive/provider/token_provider.dart';
import 'package:provider/provider.dart';

class ListDishesGrid extends StatefulWidget {
  final int restaurantId;
  final String restaurantName;

  const ListDishesGrid({
    super.key,
    required this.restaurantId,
    required this.restaurantName,
  });

  @override
  State<ListDishesGrid> createState() => _ListDishesGridState();
}

class _ListDishesGridState extends State<ListDishesGrid> {
  final RestaurantService _restaurantService = RestaurantService();
  List<RestaurantMenuItem> _dishes = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchRestaurantMenu();
  }

  Future<void> _fetchRestaurantMenu() async {
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
      final dishes = await _restaurantService.getRestaurantMenu(
        widget.restaurantId,
        userId,
        token,
      );

      setState(() {
        _dishes = dishes;
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

  Future<void> _toggleFavorite(int dishId, bool currentStatus) async {
    final tokenProvider = Provider.of<TokenProvider>(context, listen: false);
    final token = tokenProvider.token;
    final userId = tokenProvider.userId;

    if (token == null || userId == null) return;

    bool success;
    if (currentStatus) {
      success = await _restaurantService.removeFavorite(userId, dishId, token);
    } else {
      success = await _restaurantService.addFavorite(userId, dishId, token);
    }

    if (success) {
      setState(() {
        final index = _dishes.indexWhere((dish) => dish.dishId == dishId);
        if (index != -1) {
          _dishes[index] = RestaurantMenuItem(
            dishId: _dishes[index].dishId,
            dishName: _dishes[index].dishName,
            imageLink: _dishes[index].imageLink,
            sentimentScore: _dishes[index].sentimentScore,
            cuisine: _dishes[index].cuisine,
            prominentFlavor: _dishes[index].prominentFlavor,
            isFavorite: !currentStatus,
            recommendScore: _dishes[index].recommendScore,
            positiveReviews:
                _dishes[index].positiveReviews, // Added missing parameter
            totalReviews:
                _dishes[index].totalReviews, // Added missing parameter
          );
        }
      });
    } else {
      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            currentStatus
                ? 'Failed to remove favorite'
                : 'Failed to add favorite',
          ),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
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
              'Failed to load menu',
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
              onPressed: _fetchRestaurantMenu,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_dishes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.restaurant_menu, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'No dishes available',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'This restaurant hasn\'t added any dishes yet.',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return GridView.builder(
      itemCount: _dishes.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 1.25,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      itemBuilder: (context, index) {
        final dish = _dishes[index];
        return GestureDetector(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => DishPage(
                  dishId: dish.dishId,
                  dishName: dish.dishName,
                  restaurantId: widget.restaurantId,
                ),
              ),
            );
          },
          child: MenuCard(
            dishId: dish.dishId,
            imagePath: dish.imageLink ?? "assets/Logo.png",
            dishName: dish.dishName,
            cuisine: dish.cuisineDisplay,
            taste: dish.tasteDisplay,
            ratingPercent: dish.ratingPercent,
            isFavorite: dish.isFavorite,
            onFavoriteToggle: (newStatus) =>
                _toggleFavorite(dish.dishId, dish.isFavorite),
          ),
        );
      },
    );
  }
}
