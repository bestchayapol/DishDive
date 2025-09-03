import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:dishdive/Pages/Restaurant/RestaurantPage.dart';

class MapViewWidget extends StatefulWidget {
  final List<Map<String, dynamic>> restaurants;
  final bool isLoading;

  const MapViewWidget({
    super.key,
    required this.restaurants,
    this.isLoading = false,
  });

  @override
  State<MapViewWidget> createState() => _MapViewWidgetState();
}

class _MapViewWidgetState extends State<MapViewWidget> {
  late GoogleMapController mapController;

  Set<Marker> getMarkers(BuildContext context) {
    return widget.restaurants.map((r) {
      return Marker(
        markerId: MarkerId(r["name"] ?? "restaurant"),
        position: LatLng(
          (r["lat"] ?? 13.7563).toDouble(), 
          (r["lng"] ?? 100.5018).toDouble()
        ),
        icon: BitmapDescriptor.defaultMarker,
        infoWindow: InfoWindow(
          title: r["name"] ?? "Restaurant",
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => RestaurantPage(
                  restaurantId: r["id"],
                  restaurantName: r["name"],
                ),
              ),
            );
          },
        ),
      );
    }).toSet();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (widget.restaurants.isEmpty) {
      return const Center(
        child: Text(
          'No restaurants found',
          style: TextStyle(
            fontSize: 18,
            color: Colors.white,
          ),
        ),
      );
    }

    // Get initial position from first restaurant or default to Bangkok
    final firstRestaurant = widget.restaurants.isNotEmpty ? widget.restaurants.first : null;
    final initialLat = firstRestaurant?["lat"]?.toDouble() ?? 13.7563;
    final initialLng = firstRestaurant?["lng"]?.toDouble() ?? 100.5018;

    return GoogleMap(
      initialCameraPosition: CameraPosition(
        target: LatLng(initialLat, initialLng),
        zoom: 14,
      ),
      markers: getMarkers(context),
      onMapCreated: (controller) => mapController = controller,
      myLocationEnabled: false,
      zoomControlsEnabled: true,
    );
  }
}
