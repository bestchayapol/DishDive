import 'package:flutter/material.dart';
import 'package:dishdive/Utils/color_use.dart';

class KeywordsSection extends StatelessWidget {
  final List<Map<String, dynamic>> tasteKeywords;
  final List<Map<String, dynamic>> costKeywords;
  final List<Map<String, dynamic>> generalKeywords;
  final void Function(BuildContext, String, int) onKeywordTap;

  const KeywordsSection({
    super.key,
    required this.tasteKeywords,
    required this.costKeywords,
    required this.generalKeywords,
    required this.onKeywordTap,
  });

  Widget buildKeywordChips(
    BuildContext context,
    List<Map<String, dynamic>> keywords,
  ) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: keywords.map((kw) {
        return GestureDetector(
          onTap: () => onKeywordTap(context, kw['label'], kw['count']),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: colorUse.accent,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '${kw['label']} (${kw['count']})',
              style: const TextStyle(
                color: Colors.black,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Cost section
        if (costKeywords.isNotEmpty) ...[
          const Text(
            'Cost:',
            style: TextStyle(
              fontWeight: FontWeight.normal,
              fontSize: 16,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 4),
          buildKeywordChips(context, costKeywords),
          const SizedBox(height: 12),
        ],
        // Taste section
        if (tasteKeywords.isNotEmpty) ...[
          const Text(
            'Taste:',
            style: TextStyle(
              fontWeight: FontWeight.normal,
              fontSize: 16,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 4),
          buildKeywordChips(context, tasteKeywords),
          const SizedBox(height: 12),
        ],
        // General section
        if (generalKeywords.isNotEmpty) ...[
          const Text(
            'General:',
            style: TextStyle(
              fontWeight: FontWeight.normal,
              fontSize: 16,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 4),
          buildKeywordChips(context, generalKeywords),
        ],
      ],
    );
  }
}
