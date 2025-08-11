import 'package:flutter/material.dart';
import 'package:dishdive/Pages/Restaurant/RestaurantPage.dart';

class ListViewWidget extends StatelessWidget {
  const ListViewWidget({super.key});

  @override
  Widget build(BuildContext context) {
    // Placeholder: 4 blank grey cards, each navigates to RestaurantPage on tap
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: 4,
      itemBuilder: (context, index) => GestureDetector(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const RestaurantPage()),
          );
        },
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
