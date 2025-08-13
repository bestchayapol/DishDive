import 'package:flutter/material.dart';

class RestaurantCard extends StatelessWidget {
  final String name;
  final String cuisine;
  final String distance;
  final String imageUrl;
  final VoidCallback onTap;

  const RestaurantCard({
    super.key,
    required this.name,
    required this.cuisine,
    required this.distance,
    required this.imageUrl,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 18),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF6E3),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            // Restaurant image
            Container(
              width: 90,
              height: 90,
              margin: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[400],
                borderRadius: BorderRadius.circular(10),
                image: imageUrl.isNotEmpty
                    ? DecorationImage(
                        image: NetworkImage(imageUrl),
                        fit: BoxFit.cover,
                      )
                    : null,
              ),
            ),
            // Info
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  vertical: 14,
                  horizontal: 4,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        fontFamily: 'InriaSans',
                        fontWeight: FontWeight.bold,
                        fontSize: 24,
                        color: Colors.black,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      cuisine,
                      style: const TextStyle(fontSize: 18, color: Colors.black),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      distance,
                      style: const TextStyle(fontSize: 18, color: Colors.black),
                    ),
                  ],
                ),
              ),
            ),
            // Arrow button
            Padding(
              padding: const EdgeInsets.only(right: 12.0),
              child: Icon(Icons.chevron_right, size: 32, color: Colors.black),
            ),
          ],
        ),
      ),
    );
  }
}
