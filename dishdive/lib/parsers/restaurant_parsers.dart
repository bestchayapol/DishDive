import 'dart:convert';

// Parse restaurant list response (List<dynamic>) into lightweight maps used by UI
List<Map<String, dynamic>> parseRestaurantList(String rawJson) {
  final data = json.decode(rawJson) as List<dynamic>;
  return data.map<Map<String, dynamic>>((restaurant) {
    final locations = (restaurant['locations'] as List?) ?? [];
    final firstLocation = locations.isNotEmpty ? locations.first : null;
    final distKm = (firstLocation != null ? (firstLocation['distance'] as num?) : null)?.toDouble();
    final distanceText = distKm != null && distKm > 0 ? '${distKm.toStringAsFixed(1)} km away' : null;
    return {
      'id': restaurant['res_id'],
      'name': restaurant['res_name'] ?? 'Unknown Restaurant',
      'cuisine': restaurant['cuisine'] ?? 'Mixed',
      'distance': distanceText,
      'imageUrl': restaurant['image_link'] ?? '',
      'locations': locations,
      'lat': firstLocation?['latitude']?.toDouble(),
      'lng': firstLocation?['longitude']?.toDouble(),
    };
  }).toList();
}

// Parse search results (List<dynamic> of objects) into same shape
List<Map<String, dynamic>> parseSearchResults(String rawJson) {
  final data = json.decode(rawJson) as List<dynamic>;
  return data.map<Map<String, dynamic>>((restaurant) {
    final location = (restaurant['location'] ?? {}) as Map<String, dynamic>;
    final distKm = (location['distance'] as num?)?.toDouble();
    final distanceText = distKm != null && distKm > 0 ? '${distKm.toStringAsFixed(1)} km away' : null;
    return {
      'id': restaurant['res_id'],
      'name': restaurant['res_name'] ?? 'Unknown Restaurant',
      'cuisine': restaurant['cuisine'] ?? 'Mixed',
      'distance': distanceText,
      'imageUrl': restaurant['image_link'] ?? '',
      'location': location,
      'locations': [location],
      'lat': location['latitude']?.toDouble(),
      'lng': location['longitude']?.toDouble(),
    };
  }).toList();
}
