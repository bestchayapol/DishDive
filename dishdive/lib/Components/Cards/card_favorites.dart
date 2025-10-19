import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class FavoriteCard extends StatelessWidget {
  final String name;
  final int percent;
  final String tags;
  final String? imageUrl;
  final VoidCallback onDelete;

  const FavoriteCard({
    super.key,
    required this.name,
    required this.percent,
    required this.tags,
    this.imageUrl,
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
              image: imageUrl != null && imageUrl!.isNotEmpty
                  ? DecorationImage(
                      image: NetworkImage(imageUrl!),
                      fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: imageUrl == null || imageUrl!.isEmpty
                ? const Icon(Icons.restaurant, color: Colors.white, size: 30)
                : null,
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
                  const SizedBox(height: 4),
                  // Sentiment bar (consistent with CardDetails)
                  Row(
                    children: [
                      Container(
                        height: 22,
                        width: 120,
                        decoration: BoxDecoration(
                          color: colorUse.negative,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: LayoutBuilder(
                          builder: (context, constraints) {
                            final filledWidth =
                                constraints.maxWidth *
                                (percent.clamp(0, 100) / 100.0);
                            final labelText = '$percent%';
                            final bool showInside = percent >= 10;

                            return Stack(
                              children: [
                                Align(
                                  alignment: Alignment.centerLeft,
                                  child: Container(
                                    width: filledWidth,
                                    height: double.infinity,
                                    decoration: BoxDecoration(
                                      color: colorUse.positive,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  left: showInside ? 0 : filledWidth + 5,
                                  child: SizedBox(
                                    width: showInside ? filledWidth : null,
                                    child: Center(
                                      child: Text(
                                        labelText,
                                        style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
                      ),
                    ],
                  ),
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
