import 'package:flutter/material.dart';

class ListFavoritesWidget extends StatelessWidget {
  const ListFavoritesWidget({super.key});

  @override
  Widget build(BuildContext context) {
    // Placeholder: 4 blank grey cards, each navigates to RestaurantPage on tap
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 4,
      itemBuilder: (context, index) => GestureDetector(
        child: Container(
          margin: const EdgeInsets.only(bottom: 18),
          height: 100,
          decoration: BoxDecoration(
            color: Colors.grey[300],
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }
}
