import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class FavoriteCard extends StatelessWidget {
  final String name;
  final int percent;
  final String tags;
  final VoidCallback onDelete;

  const FavoriteCard({
    super.key,
    required this.name,
    required this.percent,
    required this.tags,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF6E3),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Dish image placeholder
          Container(
            width: 90,
            height: 90,
            margin: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey[400],
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          // Dish info
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 14, right: 8, bottom: 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Name and X button
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          name,
                          style: const TextStyle(
                            fontFamily: 'InriaSans',
                            fontWeight: FontWeight.bold,
                            fontSize: 24,
                            color: Colors.black,
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: onDelete,
                        child: Container(
                          width: 32,
                          height: 32,
                          decoration: BoxDecoration(
                            color: colorUse.activeButton,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(
                            Icons.close,
                            color: Colors.white,
                            size: 22,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  // Sentiment bar
                  Row(
                    children: [
                      Stack(
                        children: [
                          Container(
                            height: 18,
                            width: 120,
                            decoration: BoxDecoration(
                              color: Colors.black, // Light grey background
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          Container(
                            height: 18,
                            width: 120 * (percent / 100),
                            decoration: BoxDecoration(
                              color: colorUse.sentimentColor,
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          SizedBox(
                            height: 18,
                            width: 120,
                            child: Center(
                              child: Text(
                                "$percent%",
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  // Tags
                  Text(
                    tags,
                    style: const TextStyle(fontSize: 18, color: Colors.black),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
