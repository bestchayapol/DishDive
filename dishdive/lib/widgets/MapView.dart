import 'package:flutter/material.dart';

class MapViewWidget extends StatelessWidget {
  const MapViewWidget({super.key});

  @override
  Widget build(BuildContext context) {
    // Placeholder: big grey rectangle
    return Center(
      child: Container(
        margin: const EdgeInsets.all(24),
        height: 400,
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.grey[400],
          borderRadius: BorderRadius.circular(20),
        ),
      ),
    );
  }
}
