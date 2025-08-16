import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:dishdive/Pages/Restaurant/RestaurantPage.dart';

class MapViewWidget extends StatefulWidget {
  const MapViewWidget({super.key});

  @override
  State<MapViewWidget> createState() => _MapViewWidgetState();
}

class _MapViewWidgetState extends State<MapViewWidget> {
  late GoogleMapController mapController;

  // Example restaurant data with coordinates
  final List<Map<String, dynamic>> restaurants = [
    {"name": "Alfredo's Seafood", "lat": 13.7563, "lng": 100.5018},
    {"name": "Nayeon BBQ", "lat": 13.7570, "lng": 100.5025},
    // Add more restaurants here...
  ];

  Set<Marker> getMarkers(BuildContext context) {
    return restaurants.map((r) {
      return Marker(
        markerId: MarkerId(r["name"]),
        position: LatLng(r["lat"], r["lng"]),
        icon: BitmapDescriptor.defaultMarker, // Use a generic asset
        infoWindow: InfoWindow(
          title: r["name"],
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const RestaurantPage()),
            );
          },
        ),
      );
    }).toSet();
  }

  @override
  Widget build(BuildContext context) {
    return GoogleMap(
      initialCameraPosition: CameraPosition(
        target: LatLng(13.7563, 100.5018), // Center on first restaurant
        zoom: 14,
      ),
      markers: getMarkers(context),
      onMapCreated: (controller) => mapController = controller,
      myLocationEnabled: false,
      zoomControlsEnabled: true,
    );
  }
}
